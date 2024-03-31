# -*- coding: utf-8 -*-
# @Time : 25/03/2024 12:04
# @Author : Qingyu Zhang
# @Email : qingyu.zhang.23@ucl.ac.uk
# @Institution : UCL
# @FileName: kalman_filter.py
# @Software: PyCharm
# @Blog ：https://github.com/alfredzhang98

"""
Use this system for:
Linear system: satisfy superposition and homogeneity
Gaussian Systems: noise satisfies normal distribution

Parameters.
- Q: Estimate of the state transfer covariance matrix, defaults to 1e-5.
- R: Estimate of the observation noise covariance matrix, default is 0.1.

Methods: apply_filter(data)
- apply_filter(data): applies a Kalman filter to the given one-dimensional data and returns the filtered result.
- demo(): A static method that demonstrates how to use the Kalman filter on random data and plot the results.
"""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use('TkAgg')


class AdaptionKalmanFilter:
    """
    Need the set those parameter carefully
    """
    def __init__(self):
        self.Q = 1e-5  # State transfer covariance matrix
        self.R = 0.1  # Observation noise covariance matrix

        self.x_hat = None  # Estimated state
        self.P = None  # State Covariance
        self.K = None  # Kalman gain

        # update Way0 Suitable for large fluctuations
        self.last_measurement_error = None
        self.measurement_error_sequence = []
        self.mean_width = 10
        self.measurement_error_adapt_rate = 0.15
        self.max_q = 1e-2
        self.max_r = 10
        self.min_q = 1e-6
        self.min_r = 1e-4

        # update Way1 Suitable for processing with small fluctuations
        self.last_innovation = None
        self.innovation_sequence = []
        self.cov_width = 10
        self.target_cov = 1
        self.innovation_adapt_rate = 0.2

        # update Way2 Balance fluctuations and responses
        self.residual_adapt_rate = 1e-3

    def print_info(self):
        print(f'Q: {self.Q}, R: {self.R} '
              f' \n WAY0 \n '
              f'mean_width: {self.mean_width}, measurement_error_adapt_rate: {self.measurement_error_adapt_rate}, '
              f'max_q: {self.max_q}, max_r: {self.max_r}, min_q: {self.min_q}, min_r: {self.min_r} '
              f'\n WAY1 \n '
              f'cov_width: {self.cov_width}, target_cov: {self.target_cov}, '
              f'innovation_adapt_rate: {self.innovation_adapt_rate}'
              f' \n WAY3 \n '
              f'residual_adapt_rate: {self.residual_adapt_rate}')

    def update_value(self, attr_name, new_value):
        """
        :param attr_name:
        Q, R,
        mean_width, measurement_error_adapt_rate, max_q, max_r, min_q, min_r
        cov_width, target_cov, innovation_adapt_rate,
        residual_adapt_rate
        :param new_value:
        :return: None
        """
        setattr(self, attr_name, new_value)

    def _initialize(self, initial_value, P=1.0):
        """
        Initialise the filter state.
        """
        self.x_hat = initial_value
        self.P = P

    def _update_parameters_measurement_error(self, measurement_error):
        """
        Dynamically update the Q and R parameters based on the trend of the measurement error.
        """
        # Add the current error to the trend list
        if self.last_measurement_error is not None:
            self.measurement_error_sequence.append(measurement_error - self.last_measurement_error)

        # Maintain the length of the error trend list, considering only the N most recent measurements
        if len(self.measurement_error_sequence) > self.mean_width:
            self.measurement_error_sequence.pop(0)

        # Calculate the mean of the error trend
        if self.measurement_error_sequence:
            avg_trend = sum(self.measurement_error_sequence) / len(self.measurement_error_sequence)

            # Adjust Q and R for error trend
            if avg_trend > 0:
                # error increases, increase Q and R to accommodate uncertainty
                self.Q = min(self.Q * (1 + self.measurement_error_adapt_rate), self.max_q)  # avoid Q R growing too fast
                self.R = min(self.R * (1 + self.measurement_error_adapt_rate), self.max_r)
            elif avg_trend < 0:
                # Error reduction, reduce Q and R to improve estimation accuracy
                self.Q = max(self.Q * (1 - self.measurement_error_adapt_rate), self.min_q)
                self.R = max(self.R * (1 - self.measurement_error_adapt_rate), self.min_r)

        self.last_measurement_error = measurement_error

    def _update_parameters_innovation(self, innovation):
        """
        Dynamically update the Q and R parameters based on the cov of the innovation.
        """
        # Add the current error to the trend list
        if self.last_innovation is not None:
            self.innovation_sequence.append(innovation - self.last_innovation)

        # Maintain the length of the error trend list, considering only the N most recent measurements
        if len(self.innovation_sequence) > self.cov_width:
            self.innovation_sequence.pop(0)

        # Calculate the mean of the error trend
        if self.innovation_sequence:
            innovate_var = np.var(self.innovation_sequence[-len(self.innovation_sequence):])

            # Adjust Q and R for error trend
            if innovate_var > self.target_cov:
                self.Q *= 1 + self.innovation_adapt_rate  # increase the process noise estimate if innovate_var is
                # greater than target
                self.R *= 1 - self.innovation_adapt_rate  # decrease the observation noise estimate
            else:
                self.Q *= 1 - self.innovation_adapt_rate
                self.Q *= 1 - self.innovation_adapt_rate  # Instead, decrease the process noise estimate
                self.R *= 1 + self.innovation_adapt_rate  # and increase the observation noise estimate

        self.last_innovations = innovation

    def _update_parameters_residual(self, data, K):
        """
        Based on residual dynamically updates Q and R.
        """
        self.Q = (1 - self.residual_adapt_rate) * self.Q + self.residual_adapt_rate * (K * data) ** 2
        self.R = (1 - self.residual_adapt_rate) * self.R + self.residual_adapt_rate * ((1 - K) * data) ** 2

    def process_measurement(self, data, process_type=0):
        """
        Processes individual real-time measurements and dynamically updates Q and R.
        """
        # update the first data
        if self.x_hat is None:
            self._initialize(data)
            return self.x_hat

        # Prediction steps
        x_hat_minus = self.x_hat
        p_minus = self.P + self.Q

        # Update step
        self.K = p_minus / (p_minus + self.R)
        self.x_hat = x_hat_minus + self.K * (data - x_hat_minus)
        self.P = (1 - self.K) * p_minus

        error_abs = abs(data - self.x_hat)
        error = data - self.x_hat

        match process_type:
            case 0:
                self._update_parameters_measurement_error(error_abs)
            case 1:
                self._update_parameters_innovation(error)
            case 2:
                self._update_parameters_residual(error, self.K)
            case _:
                raise ValueError("Input the Wrong Process Type")

        return self.x_hat

    def complete_measurement(self, data):
        """
        Processes complete measurements and updates Q and R dynamically.
        """
        n = len(data)
        x_hat = np.zeros(n)  # Filtered state estimate
        P = np.zeros(n)  # Filtered state covariance matrix
        x_hat_minus = np.zeros(n)  # Predicted state estimate
        p_minus = np.zeros(n)  # Predicted state covariance matrix
        K = np.zeros(n)  # Kalman gain

        x_hat[0] = data[0]
        P[0] = 1.0

        for k in range(1, n):
            x_hat_minus[k] = x_hat[k - 1]
            p_minus[k] = P[k - 1] + self.Q
            K[k] = p_minus[k] / (p_minus[k] + self.R)
            x_hat[k] = x_hat_minus[k] + K[k] * (data[k] - x_hat_minus[k])
            P[k] = (1 - K[k]) * p_minus[k]

        return x_hat

    @staticmethod
    def demo():
        np.random.seed(42)
        true_values = np.random.uniform(10, 100, size=100)
        additional_values = np.random.uniform(900, 1000, size=200)
        additional_values2 = np.random.uniform(-300, -200, size=100)
        true_values = np.concatenate((true_values, additional_values))
        true_values = np.concatenate((true_values, additional_values2))
        noisy_measurements = true_values + np.random.normal(0, 0.05, size=true_values.shape)
        akf = AdaptionKalmanFilter()

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(true_values, label='True Values', color='g')
        ax.scatter(np.arange(len(noisy_measurements)), noisy_measurements, label='Noisy Measurements', color='r', s=10)
        line, = ax.plot([], [], label='Filtered Values', color='b')
        plt.xlabel('Time step')
        plt.ylabel('Value')
        plt.title('Adaptive Kalman Filter Demonstration')
        plt.legend()

        filtered_values = []
        for i, measurement in enumerate(noisy_measurements):
            filtered_value = akf.process_measurement(measurement, process_type=2)
            filtered_values.append(filtered_value)
            print(f"Filtered value at step {i}: {filtered_value}")  # Print filtered value
            line.set_data(np.arange(i + 1), filtered_values)
            ax.relim()
            ax.autoscale_view()
            plt.pause(0.0001)  # Reduce delay between updates

        plt.show()
        print(f"Final Q: {akf.Q}, Final R: {akf.R}")


if __name__ == "__main__":
    AdaptionKalmanFilter.demo()

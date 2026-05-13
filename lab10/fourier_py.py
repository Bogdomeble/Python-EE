# %%
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.fft import fft, fftfreq

# %%
# read signal data from csv files

fs = 1000 # sampling frequency in Hz
fs_2 = 10000 # sampling frequency for signal 2 in Hz
fs_3 = fs_2 # sampling frequency for signal 3 in Hz

signal_1_df = pd.read_csv("signal_01.csv",sep=',',on_bad_lines='warn')
signal_2_df = pd.read_csv("signal_02.csv",sep=',',on_bad_lines='warn')
signal_3_df = pd.read_csv("signal_03.csv",sep=',',on_bad_lines='warn')

# print(signal_1_df.head())

# %%
t_1 = signal_1_df["time_s"].values
y_1 = signal_1_df["signal_V"].values  

# plot this using matplotlib

plt.figure(figsize=(10, 4))
plt.plot(t_1, y_1)
plt.title('signal 1 in time domain')
plt.xlabel('Time [s]')
plt.ylabel('Voltage amplitude [V]')
plt.grid(True)
plt.show()

# %%
N = len(t_1) # number of samples

dt = t_1[1] - t_1[0] # time step

T_total = t_1[-1] - t_1[0] # total time duration of the signal

df_res = 1 / T_total # frequency resolution

print(f'{N} samples, dt = {dt:.4f} s, T_total = {T_total:.2f} s, df = {df_res:.2f} Hz')

# %%
Y = fft(y_1) # compute the FFT of the signal

frequencies = fftfreq(N, dt)[:N//2] # compute the corresponding frequencies for positive frequencies

magnitude = 2.0/N * np.abs(Y[0:N//2]) # compute the magnitude of the FFT and normalize

plt.figure(figsize=(10, 4))
plt.plot(frequencies, magnitude)
plt.title('Magnitude of the FFT of signal 1')
plt.xlabel('frequency [Hz]')
plt.ylabel('Amplitude [V]')
plt.grid(True)
plt.show()

print(f'Main frequency component: {frequencies[np.argmax(magnitude)]:.2f} Hz with amplitude {np.max(magnitude):.2f} V')
print(f'Nyquist frequency: {fs/2:.2f} Hz') # half of sampling frequency is the maximum frequency that can be accurately represented without aliasing

# %%
# signal 2

t_2 = signal_2_df["time_s"].values
y_2 = signal_2_df["signal_V"].values
N_2 = len(t_2)
dt_2 = t_2[1] - t_2[0]
T_total_2 = t_2[-1] - t_2[0]
df_res_2 = 1 / T_total_2
print(f'{N_2} samples, dt = {dt_2:.4f} s, T_total = {T_total_2:.2f} s, df = {df_res_2:.2f} Hz')

# %%
# plot signal 2 in time domain

plt.figure(figsize=(10, 4))
plt.plot(t_2, y_2)
plt.title('signal 2 in time domain')
plt.xlabel('Time [s]')
plt.ylabel('Voltage amplitude [V]')
plt.grid(True)
plt.show()

# %%
# calculate and plot FFT for signal 2

Y_2 = fft(y_2)
frequencies_2 = fftfreq(N_2, dt_2)[:N_2//2]
magnitude_2 = 2.0/N_2 * np.abs(Y_2[0:N_2//2])
plt.figure(figsize=(10, 4))
plt.plot(frequencies_2, magnitude_2)
plt.title('Magnitude of the FFT of signal 2')
plt.xlabel('frequency [Hz]')
plt.ylabel('Amplitude [V]')
plt.grid(True)
plt.show()

# %%
# spectral leakage detected - use hanning window to reduce it

window = np.hanning(N_2)
y_2_windowed = y_2 * window
Y_2_windowed = fft(y_2_windowed)

# plot the signal with hanning window in time domain to see the effect of the window

plt.figure(figsize=(10, 4))
plt.plot(t_2, y_2_windowed)
plt.title('signal 2 with Hanning window in time domain')
plt.xlabel('Time [s]')
plt.ylabel('Voltage amplitude [V]')
plt.grid(True)
plt.show()





# %%
# plot the FFT of the windowed signal to see the reduction in spectral leakage?

magnitude_2_windowed = 2.0/N_2 * np.abs(Y_2_windowed[0:N_2//2])
plt.figure(figsize=(10, 4))
plt.plot(frequencies_2, magnitude_2_windowed)
plt.title('Magnitude of the FFT of signal 2 with Hamming window')
plt.xlabel('frequency [Hz]')
plt.ylabel('Amplitude [V]')
plt.grid(True)
plt.show()



# %%




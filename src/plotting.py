""" Theoretically will contain utils for plotting stats as the AI works """

from collections import namedtuple
# import numpy as np #pylint: disable=E0401
# import pandas as pd #pylint: disable=E0401
# from matplotlib import pyplot as plt #pylint: disable=E0401
# from mpl_toolkits.mplot3d import Axes3D #pylint: disable=E0401

EpisodeStats = namedtuple("Stats", ["episode_lengths", "episode_rewards"])


# def plot_episode_stats(stats, smoothing_window=10, noshow=False):
#     # Plot the episode length over time
#     fig1 = plt.figure(figsize=(10, 5))
#     plt.plot(stats.episode_lengths)
#     plt.xlabel("Episode")
#     plt.ylabel("Episode Length")
#     plt.title("Episode Length over Time")
#     if noshow:
#         plt.close(fig1)
#     else:
#         plt.show(fig1)
#
#     # Plot the episode reward over time
#     fig2 = plt.figure(figsize=(10, 5))
#     rewards_smoothed = pd.Series(stats.episode_rewards).rolling(smoothing_window, min_periods=smoothing_window).mean()
#     plt.plot(rewards_smoothed)
#     plt.xlabel("Episode")
#     plt.ylabel("Episode Reward (Smoothed)")
#     plt.title("Episode Reward over Time (Smoothed over window size {})".format(smoothing_window))
#     if noshow:
#         plt.close(fig2)
#     else:
#         plt.show(fig2)
#
#     # Plot time steps and episode number
#     fig3 = plt.figure(figsize=(10, 5))
#     plt.plot(np.cumsum(stats.episode_lengths), np.arange(len(stats.episode_lengths)))
#     plt.xlabel("Time Steps")
#     plt.ylabel("Episode")
#     plt.title("Episode per time step")
#     if noshow:
#         plt.close(fig3)
#     else:
#         plt.show(fig3)

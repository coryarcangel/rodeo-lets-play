# https://www.tensorflow.org/agents/tutorials/1_dqn_tutorial

from __future__ import absolute_import, division, print_function

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import PIL.Image
import pyvirtualdisplay

import tensorflow as tf

from tf_agents.agents.dqn import dqn_agent
from tf_agents.drivers import dynamic_step_driver
from tf_agents.environments import suite_gym
from tf_agents.environments import tf_py_environment
from tf_agents.eval import metric_utils
from tf_agents.metrics import tf_metrics
from tf_agents.networks import q_network
from tf_agents.policies import random_tf_policy
from tf_agents.policies.policy_saver import PolicySaver
from tf_agents.replay_buffers import tf_uniform_replay_buffer
from tf_agents.trajectories import trajectory
from tf_agents.utils import common


tf.compat.v1.enable_v2_behavior()

# Set up a virtual display for rendering OpenAI gym environments.
display = pyvirtualdisplay.Display(visible=0, size=(1400, 900)).start()


num_iterations = 20000  # @param {type:"integer"}

initial_collect_steps = 100  # @param {type:"integer"}
collect_steps_per_iteration = 1  # @param {type:"integer"}
replay_buffer_max_length = 100000  # @param {type:"integer"}

batch_size = 64  # @param {type:"integer"}
learning_rate = 1e-3  # @param {type:"number"}
log_interval = 200  # @param {type:"integer"}

num_eval_episodes = 10  # @param {type:"integer"}
eval_interval = 1000  # @param {type:"integer"}

# https://www.tensorflow.org/agents/api_docs/python/tf_agents/networks/q_network/QNetwork
fc_layer_params = (100,)

saved_policy_name = 'saved_deepq_policy.txt'

# Options are AdamOptimizer, GradientDescentOptimizer, MomentumOptimizer, etc.
# https://www.tensorflow.org/api_docs/python/tf/compat/v1/train/AdamOptimizer
optimizer = tf.compat.v1.train.AdamOptimizer(learning_rate=learning_rate)

env_name = 'CartPole-v0'
env = suite_gym.load(env_name)


env.reset()
PIL.Image.fromarray(env.render())


print('Observation Spec:')
print(env.time_step_spec().observation)


print('Reward Spec:')
print(env.time_step_spec().reward)


print('Action Spec:')
print(env.action_spec())


time_step = env.reset()
print('Time step:')
print(time_step)

action = np.array(1, dtype=np.int32)

next_time_step = env.step(action)
print('Next time step:')
print(next_time_step)


train_py_env = suite_gym.load(env_name)
eval_py_env = suite_gym.load(env_name)


train_env = tf_py_environment.TFPyEnvironment(train_py_env)
eval_env = tf_py_environment.TFPyEnvironment(eval_py_env)


# Other Options are CriticNetworks, ActorNetworks, ActorDistributionNetworks
q_net = q_network.QNetwork(
    train_env.observation_spec(),
    train_env.action_spec(),
    fc_layer_params=fc_layer_params)


train_step_counter = tf.Variable(0)

agent = dqn_agent.DqnAgent(
    train_env.time_step_spec(),
    train_env.action_spec(),
    q_network=q_net,
    optimizer=optimizer,
    td_errors_loss_fn=common.element_wise_squared_loss,
    train_step_counter=train_step_counter)

agent.initialize()


eval_policy = agent.policy
collect_policy = agent.collect_policy


random_policy = random_tf_policy.RandomTFPolicy(train_env.time_step_spec(),
                                                train_env.action_spec())


def compute_avg_return(environment, policy, num_episodes=10):
    total_return = 0.0
    for _ in range(num_episodes):
        time_step = environment.reset()
        episode_return = 0.0

        while not time_step.is_last():
            action_step = policy.action(time_step)
            time_step = environment.step(action_step.action)
            episode_return += time_step.reward

        total_return += episode_return

    avg_return = total_return / num_episodes
    return avg_return.numpy()[0]


compute_avg_return(eval_env, random_policy, num_eval_episodes)


replay_buffer = tf_uniform_replay_buffer.TFUniformReplayBuffer(
    data_spec=agent.collect_data_spec,
    batch_size=train_env.batch_size,
    max_length=replay_buffer_max_length)


agent.collect_data_spec

agent.collect_data_spec._fields


def collect_step(environment, policy, buffer):
    time_step = environment.current_time_step()
    action_step = policy.action(time_step)
    next_time_step = environment.step(action_step.action)
    traj = trajectory.from_transition(time_step, action_step, next_time_step)

    # Add trajectory to the replay buffer
    buffer.add_batch(traj)


def collect_data(env, policy, buffer, steps):
    for _ in range(steps):
        collect_step(env, policy, buffer)


collect_data(train_env, random_policy, replay_buffer, initial_collect_steps)


# Dataset generates trajectories with shape [Bx2x...]
dataset = replay_buffer.as_dataset(
    num_parallel_calls=3,
    sample_batch_size=batch_size,
    num_steps=2).prefetch(3)

dataset


iterator = iter(dataset)

print(iterator)


# (Optional) Optimize by wrapping some of the code in a graph using TF function
agent.train = common.function(agent.train)


def train_model():
    # Reset the train step
    agent.train_step_counter.assign(0)

    # Evaluate the agent's policy once before training.
    avg_return = compute_avg_return(eval_env, agent.policy, num_eval_episodes)
    returns = [avg_return]

    for _ in range(num_iterations):
        # Collect a few steps using collect_policy and save to the replay buff
        collect_data(train_env, agent.collect_policy, replay_buffer, collect_steps_per_iteration)

        # Sample a batch of data from the buffer and update the agent's network
        experience, unused_info = next(iterator)
        train_loss = agent.train(experience).loss

        step = agent.train_step_counter.numpy()

        if step % log_interval == 0:
            print('step = {0}: loss = {1}'.format(step, train_loss))

        if step % eval_interval == 0:
            avg_return = compute_avg_return(eval_env, agent.policy, num_eval_episodes)
            print('step = {0}: Average Return = {1}'.format(step, avg_return))
            returns.append(avg_return)

    return returns


def save_model():
    # https://www.tensorflow.org/agents/api_docs/python/tf_agents/policies/policy_saver/PolicySaver

    saver = PolicySaver(
        collect_policy,
        batch_size=batch_size,
        train_step=agent.train_step_counter.numpy()
    )

    saver.save(saved_policy_name)


def load_model():
    # saved_policy = tf.compat.v2.saved_model.load(saved_policy_name)
    pass


def plot_model(returns):
    iterations = range(0, num_iterations + 1, eval_interval)
    plt.plot(iterations, returns)
    plt.ylabel('Average Return')
    plt.xlabel('Iterations')
    plt.ylim(top=250)


returns = train_model()

save_model()

plot_model(returns)

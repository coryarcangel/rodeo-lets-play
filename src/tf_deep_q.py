import logging
import os
import tensorflow as tf

from tf_agents.agents.dqn import dqn_agent
from tf_agents.drivers import dynamic_step_driver
from tf_agents.environments import tf_py_environment
from tf_agents.metrics import py_metrics
from tf_agents.networks import q_network
from tf_agents.policies import policy_saver
from tf_agents.replay_buffers import tf_uniform_replay_buffer
from tf_agents.utils import common


def load_saved_policy(policy_dir):
    saved_policy = tf.compat.v2.saved_model.load(policy_dir)
    return saved_policy


def compute_avg_return(env, policy, max_episode_length=100, num_episodes=10):
    total_return = 0.0
    for _ in range(num_episodes):
        time_step = env.reset()
        episode_return = 0.0
        episode_length = 0
        while not time_step.is_last() and episode_length < max_episode_length:
            action_step = policy.action(time_step)
            time_step = env.step(action_step.action)
            episode_return += time_step.reward
            episode_length += 1
    total_return += episode_return

    avg_return = total_return / num_episodes
    return avg_return.numpy()[0]


# https://www.tensorflow.org/agents/tutorials/10_checkpointer_policysaver_tutorial
class TfAgentDeepQManager(object):
    def __init__(self, env, params={}):
        def p_val(key, defaultVal):
            return params[key] if key in params else defaultVal

        self.logger = logging.getLogger('TfAgentDeepQManager')
        self.env = env
        self.tf_env = tf_py_environment.TFPyEnvironment(env)

        # Agent Params
        fc_layer_params = p_val('fc_layer_params', (100,))
        learning_rate = p_val('learning_rate', 1e-3)
        errors_loss_fn = p_val('errors_loss_fn', common.element_wise_squared_loss)

        # Training Params
        collect_steps_per_iteration = p_val('collect_steps_per_iteration', 100)
        replay_buffer_capacity = p_val('replay_buffer_capacity', 100000)
        self.replay_batch_size = p_val('replay_batch_size', 64)
        self.train_log_interval = p_val('train_log_interval', 5)
        self.train_eval_interval = p_val('train_eval_interval', 1000)
        num_eval_episodes = p_val('num_eval_episodes', 10)

        # Saving / Loading Params
        save_dir = self.save_dir = p_val('save_dir', os.getcwd() + '/deep_q_save')
        max_checkpoints = p_val('max_checkpoints', 1)

        self.q_net = q_network.QNetwork(
            self.tf_env.observation_spec(),
            self.tf_env.action_spec(),
            fc_layer_params=fc_layer_params)

        self.optimizer = tf.compat.v1.train.AdamOptimizer(learning_rate=learning_rate)

        global_step = tf.compat.v1.train.get_or_create_global_step()
        self.train_step_counter = global_step
        # self.train_step_counter = tf.Variable(0)

        agent = self.agent = dqn_agent.DqnAgent(
            self.tf_env.time_step_spec(),
            self.tf_env.action_spec(),
            q_network=self.q_net,
            optimizer=self.optimizer,
            td_errors_loss_fn=errors_loss_fn,
            train_step_counter=self.train_step_counter)
        self.agent.initalize()

        agent.train = common.function(agent.train)

        self.replay_buffer = tf_uniform_replay_buffer.TFUniformReplayBuffer(
            data_spec=agent.collect_data_spec,
            batch_size=self.tf_env.batch_size,
            max_length=replay_buffer_capacity)

        self.avg_return_metric = py_metrics.AverageReturnMetric(
            buffer_size=num_eval_episodes)

        self.collect_driver = dynamic_step_driver.DynamicStepDriver(
            self.tf_env,
            agent.collect_policy,
            observers=[self.replay_buffer.add_batch, self.avg_return_metric],
            num_steps=collect_steps_per_iteration)

        self.has_collected_initial_data = False

        checkpoint_dir = os.path.join(save_dir, 'checkpoint')
        self.train_checkpointer = common.Checkpointer(
            ckpt_dir=checkpoint_dir,
            max_to_keep=max_checkpoints,
            agent=agent,
            policy=agent.policy,
            replay_buffer=self.replay_buffer,
            global_step=global_step
        )

        self.policy_saver = policy_saver.PolicySaver(agent.policy)

    def collect_initial_data(self):
        # Initial data collection
        self.collect_driver.run()

        # Dataset generates trajectories with shape [BxTx...] where
        # T = n_step_update + 1.
        self.replay_dataset = self.replay_buffer.as_dataset(
            num_parallel_calls=3, sample_batch_size=self.replay_batch_size,
            num_steps=2).prefetch(3)

        self.replay_iterator = iter(self.replay_dataset)

        self.has_collected_initial_data = True

    def train(self, num_iterations=200):
        if not self.has_collected_initial_data:
            self.collect_initial_data()

        # Reset the train step
        self.agent.train_step_counter.assign(0)

        # Evaluate the agent's policy once before training
        returns = [self.avg_return_metric.result()]

        for _ in range(num_iterations):
            # Collect a few steps, save to the replay buffer
            self.collect_driver.run()

            # Sample batch of data from buffer and update the agent's network
            experience, unused_info = next(self.replay_iterator)
            train_loss = self.agent.train(experience).loss

            step = self.agent.train_step_counter.numpy()

            if step % self.train_log_interval == 0:
                self.logger.info('step = {0}: loss = {1}'.format(
                    step, train_loss))

            if step % self.train_eval_interval == 0:
                avg_return = self.avg_return_metric.result()
                self.logger.info('step = {0}: Average Return = {1}'.format(
                    step, avg_return))
                returns.append(avg_return)

    def save_policy(self, name='policy'):
        policy_save_dir = os.path.join(self.save_dir, name)
        self.policy_saver.save(policy_save_dir)

    def load_policy(self, name='policy'):
        policy_save_dir = os.path.join(self.save_dir, name)
        return load_saved_policy(policy_save_dir)

    def save_checkpoint(self):
        self.train_checkpointer.save(self.train_step_counter)

    def restore_checkpoint(self):
        self.train_checkpointer.initialize_or_restore()
        self.train_step_counter = tf.compat.v1.train.get_global_step()

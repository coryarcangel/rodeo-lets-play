import tensorflow as tf

from tf_agents.agents.dqn import dqn_agent
from tf_agents.networks import q_network
from tf_agents.utils import common


class TfAgentDeepQCreator(object):
    def __init__(self, env, params={}):
        self.env = env

        def get_param_val(key, defaultVal):
            return params[key] if key in params else defaultVal

        fc_layer_params = get_param_val('fc_layer_params', (100,))
        learning_rate = get_param_val('learning_rate', 1e-3)
        errors_loss_fn = get_param_val('errors_loss_fn', common.element_wise_squared_loss)

        self.q_net = q_network.QNetwork(
            env.observation_spec(),
            env.action_spec(),
            fc_layer_params=fc_layer_params)

        self.optimizer = tf.compat.v1.train.AdamOptimizer(learning_rate=learning_rate)

        self.train_step_counter = tf.Variable(0)

        self.agent = dqn_agent.DqnAgent(
            env.time_step_spec(),
            env.action_spec(),
            q_network=self.q_net,
            optimizer=self.optimizer,
            td_errors_loss_fn=errors_loss_fn,
            train_step_counter=self.train_step_counter)

    def initalize(self):
        self.agent.initalize()

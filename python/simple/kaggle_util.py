from kaggle_environments import make


def make_env(seed=562124210):
    return make("lux_ai_2021", configuration={"seed": seed, "loglevel": 2, "annotations": True}, debug=True)


def run(env, agent1=None, agent2=None, width=1000, height=800, seed=562124210):
    if not agent1:
        agent1 = "simple_agent"
    if not agent2:
        agent2 = "simple_agent"
    steps = env.run([agent1, agent2])
    return steps


def show(env, width, height):
    env.render(mode="ipython", width=width, height=height)


if __name__ == '__main__':
    env = make("lux_ai_2021", configuration={"seed": 101, "loglevel": 2, "annotations": True}, debug=True)
    env.run(["simple_agent", "simple_agent"])

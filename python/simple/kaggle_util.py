from kaggle_environments import make


if __name__ == '__main__':
    env = make("lux_ai_2021", configuration={"seed": 101, "loglevel": 2, "annotations": True}, debug=True)
    env.run(["simple_agent", "simple_agent"])


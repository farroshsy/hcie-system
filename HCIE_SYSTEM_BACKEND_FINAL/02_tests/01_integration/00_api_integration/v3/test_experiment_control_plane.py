from app.api.v3.experiment_control_plane import (
    ExperimentConfig,
    ExperimentRun,
    get_all_experiment_configs,
    get_experiment_config,
    create_experiment_run,
)


def test_get_all_experiment_configs_returns_typed_configs():
    configs = get_all_experiment_configs()
    assert len(configs) > 0
    for config in configs:
        assert isinstance(config, ExperimentConfig)
        assert config.version.startswith("1.")
        assert config.config_id


def test_get_experiment_config_by_id():
    config = get_experiment_config("epsilon_sweep_v1")
    assert config.config_id == "epsilon_sweep_v1"
    assert config.version == "1.0"
    assert config.enabled is True
    assert config.parameters


def test_create_experiment_run_generates_run_id():
    config = ExperimentConfig(
        config_id="test_config",
        version="1.0",
        enabled=True,
        parameters={"epsilon": 0.1},
    )
    run = create_experiment_run(config)
    assert isinstance(run, ExperimentRun)
    assert run.run_id.startswith("run_")
    assert run.config_id == "test_config"
    assert run.status == "initialized"
    assert run.start_time is not None

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass
from pathlib import Path

from isaacsim.simulation_app import SimulationApp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 5 randomized Isaac Sim ROS2 bridge scene")
    parser.add_argument("--trial-id", type=int, default=0, help="Trial index to reproduce")
    parser.add_argument("--seed", type=int, default=0, help="Global randomization seed")
    parser.add_argument("--target-label", default="cube", help="Semantic target label recorded in reports")
    parser.add_argument("--headless", action="store_true", help="Run Isaac Sim without a UI")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--save-usd", type=str, default="", help="Optional path to save the generated USD")
    return parser.parse_args()


ARGS = parse_args()
SIMULATION_APP = SimulationApp(
    {
        "headless": ARGS.headless,
        "width": ARGS.width,
        "height": ARGS.height,
        "renderer": "RaytracedLighting",
    }
)

import carb  # noqa: E402
import omni.graph.core as og  # noqa: E402
import omni.kit.app  # noqa: E402
import omni.timeline  # noqa: E402
import omni.usd  # noqa: E402
from pxr import Gf, Sdf, UsdGeom, UsdLux, UsdPhysics  # noqa: E402


PANDA_PRIM_PATH = "/panda"
CAMERA_PRIM_PATH = "/World/camera_color_optical_frame"
BASE_FRAME = "base_link"
CAMERA_FRAME = "camera_color_optical_frame"
RGB_TOPIC = "/camera/image_raw"
DEPTH_TOPIC = "/camera/depth/image_rect_raw"
CAMERA_INFO_TOPIC = "/camera/color/camera_info"
JOINT_COMMAND_TOPIC = "/joint_command"


@dataclass(frozen=True)
class TrialSceneConfig:
    trial_id: int
    seed: int
    light_intensity: float
    table_color: tuple[float, float, float]
    object_color: tuple[float, float, float]
    camera_position: tuple[float, float, float]
    camera_rotation: tuple[float, float, float]
    target_label: str


def main() -> None:
    trial = make_trial_scene_config(ARGS.trial_id, ARGS.seed, ARGS.target_label)
    enable_ros2_bridge()
    clear_stage()
    setup_stage_units()
    add_lighting(trial)
    add_ground(trial)
    add_table(trial)
    add_objects(trial)
    add_panda()
    add_camera(trial)
    create_clock_graph()
    create_camera_graph()
    create_tf_graph(trial)
    create_joint_control_graph()

    if ARGS.save_usd:
        save_stage(ARGS.save_usd)

    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    carb.log_info(
        "Stage 5 randomized scene is running: "
        f"trial_id={trial.trial_id}, seed={trial.seed}, target_label={trial.target_label}"
    )
    carb.log_info(
        "Expected ROS2 topics: /camera/image_raw, /camera/depth/image_rect_raw, "
        "/camera/color/camera_info, /joint_states, /joint_command, /tf, /clock"
    )

    try:
        while SIMULATION_APP.is_running():
            SIMULATION_APP.update()
    finally:
        timeline.stop()
        SIMULATION_APP.close()


def make_trial_scene_config(trial_id: int, seed: int, target_label: str) -> TrialSceneConfig:
    trial_seed = _derive_trial_seed(seed, trial_id)
    rng = random.Random(trial_seed)
    return TrialSceneConfig(
        trial_id=trial_id,
        seed=trial_seed,
        light_intensity=rng.uniform(250.0, 900.0),
        table_color=(rng.uniform(0.25, 0.75), rng.uniform(0.25, 0.75), rng.uniform(0.25, 0.75)),
        object_color=(rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95)),
        camera_position=(
            0.55 + rng.uniform(-0.05, 0.05),
            -0.95 + rng.uniform(-0.05, 0.05),
            0.95 + rng.uniform(-0.04, 0.04),
        ),
        camera_rotation=(
            62.0 + rng.uniform(-4.0, 4.0),
            rng.uniform(-3.0, 3.0),
            rng.uniform(-3.0, 3.0),
        ),
        target_label=target_label,
    )


def _derive_trial_seed(seed: int, trial_id: int) -> int:
    rng = random.Random(seed)
    value = 0
    for _ in range(trial_id + 1):
        value = rng.randint(0, 2**31 - 1)
    return value


def enable_ros2_bridge() -> None:
    extension_manager = omni.kit.app.get_app().get_extension_manager()
    for extension_name in ("isaacsim.ros2.bridge", "omni.isaac.ros2_bridge"):
        try:
            extension_manager.set_extension_enabled_immediate(extension_name, True)
            carb.log_info(f"Enabled Isaac Sim extension: {extension_name}")
            return
        except Exception:  # noqa: BLE001 - extension name differs across Isaac Sim releases.
            continue
    raise RuntimeError("Could not enable Isaac Sim ROS2 bridge extension")


def clear_stage() -> None:
    stage = omni.usd.get_context().get_stage()
    for prim in list(stage.GetPseudoRoot().GetChildren()):
        stage.RemovePrim(prim.GetPath())


def setup_stage_units() -> None:
    stage = omni.usd.get_context().get_stage()
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdPhysics.Scene.Define(stage, Sdf.Path("/World/physicsScene"))


def add_lighting(trial: TrialSceneConfig) -> None:
    stage = omni.usd.get_context().get_stage()
    dome = UsdLux.DomeLight.Define(stage, "/World/DomeLight")
    dome.CreateIntensityAttr(trial.light_intensity * 0.55)
    key = UsdLux.DistantLight.Define(stage, "/World/KeyLight")
    key.CreateIntensityAttr(trial.light_intensity)
    key.CreateAngleAttr(0.5)


def add_ground(trial: TrialSceneConfig) -> None:
    stage = omni.usd.get_context().get_stage()
    plane = UsdGeom.Mesh.Define(stage, "/World/GroundPlane")
    UsdGeom.Xformable(plane).AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, -0.02))
    plane.CreatePointsAttr(
        [
            Gf.Vec3f(-2.0, -2.0, 0.0),
            Gf.Vec3f(2.0, -2.0, 0.0),
            Gf.Vec3f(2.0, 2.0, 0.0),
            Gf.Vec3f(-2.0, 2.0, 0.0),
        ]
    )
    plane.CreateFaceVertexCountsAttr([4])
    plane.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    plane.CreateDisplayColorAttr([Gf.Vec3f(*(min(component + 0.12, 1.0) for component in trial.table_color))])


def add_table(trial: TrialSceneConfig) -> None:
    add_cube("/World/TableTop", position=(0.55, 0.0, 0.37), scale=(0.7, 0.9, 0.06), color=trial.table_color)
    leg_color = tuple(max(component - 0.12, 0.0) for component in trial.table_color)
    for name, x, y in (
        ("LegFL", 0.25, 0.35),
        ("LegFR", 0.85, 0.35),
        ("LegBL", 0.25, -0.35),
        ("LegBR", 0.85, -0.35),
    ):
        add_cube(f"/World/Table{name}", position=(x, y, 0.17), scale=(0.06, 0.06, 0.34), color=leg_color)


def add_objects(trial: TrialSceneConfig) -> None:
    add_cube("/World/target_cube", position=(0.58, 0.05, 0.45), scale=(0.08, 0.08, 0.08), color=trial.object_color)
    add_cube("/World/distractor_left", position=(0.43, -0.18, 0.45), scale=(0.07, 0.07, 0.07), color=(0.9, 0.05, 0.05))
    add_cube("/World/distractor_right", position=(0.72, 0.20, 0.45), scale=(0.07, 0.07, 0.07), color=(0.05, 0.25, 0.9))


def add_cube(path: str, position: tuple[float, float, float], scale: tuple[float, float, float], color: tuple[float, float, float]) -> None:
    stage = omni.usd.get_context().get_stage()
    cube = UsdGeom.Cube.Define(stage, path)
    cube.CreateSizeAttr(1.0)
    xform = UsdGeom.Xformable(cube)
    xform.AddTranslateOp().Set(Gf.Vec3d(*position))
    xform.AddScaleOp().Set(Gf.Vec3f(*scale))
    cube.CreateDisplayColorAttr([Gf.Vec3f(*color)])


def add_panda() -> None:
    asset_path = get_isaac_asset_path("Isaac/Robots/Franka/franka_alt_fingers.usd")
    stage = omni.usd.get_context().get_stage()
    stage.DefinePrim(PANDA_PRIM_PATH, "Xform")
    prim = stage.GetPrimAtPath(PANDA_PRIM_PATH)
    prim.GetReferences().AddReference(asset_path)
    xform = UsdGeom.Xformable(prim)
    xform.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.0))
    xform.AddRotateZOp().Set(0.0)


def get_isaac_asset_path(relative_path: str) -> str:
    try:
        from isaacsim.storage.native import get_assets_root_path
    except ImportError:
        from omni.isaac.core.utils.nucleus import get_assets_root_path

    root = get_assets_root_path()
    if root is None:
        raise RuntimeError("Isaac Sim assets root is unavailable. Check the Nucleus/asset installation.")
    return f"{root.rstrip('/')}/{relative_path}"


def add_camera(trial: TrialSceneConfig) -> None:
    stage = omni.usd.get_context().get_stage()
    camera = UsdGeom.Camera.Define(stage, CAMERA_PRIM_PATH)
    camera.CreateFocalLengthAttr(24.0)
    camera.CreateHorizontalApertureAttr(20.955)
    camera.CreateVerticalApertureAttr(15.7)
    xform = UsdGeom.Xformable(camera)
    xform.AddTranslateOp().Set(Gf.Vec3d(*trial.camera_position))
    xform.AddRotateXYZOp().Set(Gf.Vec3f(*trial.camera_rotation))


def create_clock_graph() -> None:
    og.Controller.edit(
        {"graph_path": "/ROS2ClockGraph", "evaluator_name": "execution"},
        {
            og.Controller.Keys.CREATE_NODES: [
                ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
                ("PublishClock", "isaacsim.ros2.bridge.ROS2PublishClock"),
            ],
            og.Controller.Keys.CONNECT: [
                ("OnPlaybackTick.outputs:tick", "PublishClock.inputs:execIn"),
                ("ReadSimTime.outputs:simulationTime", "PublishClock.inputs:timeStamp"),
            ],
        },
    )


def create_camera_graph() -> None:
    og.Controller.edit(
        {"graph_path": "/ROS2CameraGraph", "evaluator_name": "execution"},
        {
            og.Controller.Keys.CREATE_NODES: [
                ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ("CreateRenderProduct", "isaacsim.core.nodes.IsaacCreateRenderProduct"),
                ("RGBPublisher", "isaacsim.ros2.bridge.ROS2CameraHelper"),
                ("DepthPublisher", "isaacsim.ros2.bridge.ROS2CameraHelper"),
                ("CameraInfoPublisher", "isaacsim.ros2.bridge.ROS2CameraInfoHelper"),
            ],
            og.Controller.Keys.CONNECT: [
                ("OnPlaybackTick.outputs:tick", "RGBPublisher.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "DepthPublisher.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "CameraInfoPublisher.inputs:execIn"),
                ("CreateRenderProduct.outputs:renderProductPath", "RGBPublisher.inputs:renderProductPath"),
                ("CreateRenderProduct.outputs:renderProductPath", "DepthPublisher.inputs:renderProductPath"),
                ("CreateRenderProduct.outputs:renderProductPath", "CameraInfoPublisher.inputs:renderProductPath"),
            ],
            og.Controller.Keys.SET_VALUES: [
                ("CreateRenderProduct.inputs:cameraPrim", CAMERA_PRIM_PATH),
                ("CreateRenderProduct.inputs:enabled", True),
                ("CreateRenderProduct.inputs:width", ARGS.width),
                ("CreateRenderProduct.inputs:height", ARGS.height),
                ("RGBPublisher.inputs:type", "rgb"),
                ("RGBPublisher.inputs:topicName", RGB_TOPIC),
                ("RGBPublisher.inputs:frameId", CAMERA_FRAME),
                ("DepthPublisher.inputs:type", "depth"),
                ("DepthPublisher.inputs:topicName", DEPTH_TOPIC),
                ("DepthPublisher.inputs:frameId", CAMERA_FRAME),
                ("CameraInfoPublisher.inputs:topicName", CAMERA_INFO_TOPIC),
                ("CameraInfoPublisher.inputs:frameId", CAMERA_FRAME),
            ],
        },
    )


def create_tf_graph(trial: TrialSceneConfig) -> None:
    roll, pitch, yaw = (math.radians(value) for value in trial.camera_rotation)
    og.Controller.edit(
        {"graph_path": "/ROS2TFGraph", "evaluator_name": "execution"},
        {
            og.Controller.Keys.CREATE_NODES: [
                ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
                ("PublishCameraTF", "isaacsim.ros2.bridge.ROS2PublishRawTransformTree"),
            ],
            og.Controller.Keys.CONNECT: [
                ("OnPlaybackTick.outputs:tick", "PublishCameraTF.inputs:execIn"),
                ("ReadSimTime.outputs:simulationTime", "PublishCameraTF.inputs:timeStamp"),
            ],
            og.Controller.Keys.SET_VALUES: [
                ("PublishCameraTF.inputs:parentFrameId", BASE_FRAME),
                ("PublishCameraTF.inputs:childFrameId", CAMERA_FRAME),
                ("PublishCameraTF.inputs:translation", list(trial.camera_position)),
                ("PublishCameraTF.inputs:rotation", euler_xyz_to_quaternion_ijkr(roll, pitch, yaw)),
            ],
        },
    )


def create_joint_control_graph() -> None:
    og.Controller.edit(
        {"graph_path": "/ROS2JointControlGraph", "evaluator_name": "execution"},
        {
            og.Controller.Keys.CREATE_NODES: [
                ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ("PublishJointState", "isaacsim.ros2.bridge.ROS2PublishJointState"),
                ("SubscribeJointState", "isaacsim.ros2.bridge.ROS2SubscribeJointState"),
                ("ArticulationController", "isaacsim.core.nodes.IsaacArticulationController"),
                ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
            ],
            og.Controller.Keys.CONNECT: [
                ("OnPlaybackTick.outputs:tick", "PublishJointState.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "SubscribeJointState.inputs:execIn"),
                ("OnPlaybackTick.outputs:tick", "ArticulationController.inputs:execIn"),
                ("ReadSimTime.outputs:simulationTime", "PublishJointState.inputs:timeStamp"),
                ("SubscribeJointState.outputs:jointNames", "ArticulationController.inputs:jointNames"),
                ("SubscribeJointState.outputs:positionCommand", "ArticulationController.inputs:positionCommand"),
                ("SubscribeJointState.outputs:velocityCommand", "ArticulationController.inputs:velocityCommand"),
                ("SubscribeJointState.outputs:effortCommand", "ArticulationController.inputs:effortCommand"),
            ],
            og.Controller.Keys.SET_VALUES: [
                ("ArticulationController.inputs:robotPath", PANDA_PRIM_PATH),
                ("PublishJointState.inputs:targetPrim", PANDA_PRIM_PATH),
                ("SubscribeJointState.inputs:topicName", JOINT_COMMAND_TOPIC),
            ],
        },
    )


def euler_xyz_to_quaternion_ijkr(roll: float, pitch: float, yaw: float) -> list[float]:
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)

    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    w = cr * cp * cy + sr * sp * sy
    return [x, y, z, w]


def save_stage(path: str) -> None:
    output = Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    omni.usd.get_context().save_as_stage(str(output))
    carb.log_info(f"Saved generated stage to {output}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import math
from pathlib import Path

from isaacsim.simulation_app import SimulationApp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 3 Isaac Sim ROS2 bridge scene")
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


def main() -> None:
    enable_ros2_bridge()
    clear_stage()
    setup_stage_units()
    add_lighting()
    add_ground()
    add_table()
    add_objects()
    add_panda()
    add_camera()
    create_clock_graph()
    create_camera_graph()
    create_tf_graph()
    create_joint_control_graph()

    if ARGS.save_usd:
        save_stage(ARGS.save_usd)

    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    carb.log_info("Stage 3 Isaac Sim scene is running")
    carb.log_info("Expected ROS2 topics: /camera/image_raw, /camera/depth/image_rect_raw, "
                  "/camera/color/camera_info, /joint_states, /joint_command, /tf, /clock")

    try:
        while SIMULATION_APP.is_running():
            SIMULATION_APP.update()
    finally:
        timeline.stop()
        SIMULATION_APP.close()


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


def add_lighting() -> None:
    stage = omni.usd.get_context().get_stage()
    dome = UsdLux.DomeLight.Define(stage, "/World/DomeLight")
    dome.CreateIntensityAttr(400.0)
    key = UsdLux.DistantLight.Define(stage, "/World/KeyLight")
    key.CreateIntensityAttr(800.0)
    key.CreateAngleAttr(0.5)


def add_ground() -> None:
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


def add_table() -> None:
    add_cube("/World/TableTop", position=(0.55, 0.0, 0.37), scale=(0.7, 0.9, 0.06), color=(0.55, 0.45, 0.35))
    for name, x, y in (
        ("LegFL", 0.25, 0.35),
        ("LegFR", 0.85, 0.35),
        ("LegBL", 0.25, -0.35),
        ("LegBR", 0.85, -0.35),
    ):
        add_cube(f"/World/Table{name}", position=(x, y, 0.17), scale=(0.06, 0.06, 0.34), color=(0.45, 0.35, 0.25))


def add_objects() -> None:
    add_cube("/World/red_cube", position=(0.45, -0.18, 0.45), scale=(0.08, 0.08, 0.08), color=(0.9, 0.05, 0.05))
    add_cube("/World/green_cube", position=(0.58, 0.05, 0.45), scale=(0.08, 0.08, 0.08), color=(0.05, 0.75, 0.1))
    add_cube("/World/blue_cube", position=(0.72, 0.20, 0.45), scale=(0.08, 0.08, 0.08), color=(0.05, 0.25, 0.9))


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


def add_camera() -> None:
    stage = omni.usd.get_context().get_stage()
    camera = UsdGeom.Camera.Define(stage, CAMERA_PRIM_PATH)
    camera.CreateFocalLengthAttr(24.0)
    camera.CreateHorizontalApertureAttr(20.955)
    camera.CreateVerticalApertureAttr(15.7)
    xform = UsdGeom.Xformable(camera)
    xform.AddTranslateOp().Set(Gf.Vec3d(0.55, -0.95, 0.95))
    xform.AddRotateXYZOp().Set(Gf.Vec3f(62.0, 0.0, 0.0))


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


def create_tf_graph() -> None:
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
                ("PublishCameraTF.inputs:translation", [0.55, -0.95, 0.95]),
                ("PublishCameraTF.inputs:rotation", euler_xyz_to_quaternion_ijkr(math.radians(62.0), 0.0, 0.0)),
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

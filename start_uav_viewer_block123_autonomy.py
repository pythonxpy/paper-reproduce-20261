import argparse
import math
import sys
import time
import traceback
from pathlib import Path

import numpy as np

sys.path.insert(0, "/root/paper-reproduce-20261/third_party/CityGaussian")
sys.path.insert(0, "/root/autodl-tmp/citygaussian_uav/scripts")

from internal.viewer.viewer import Viewer
from uav_autonomy import Autopilot, plan_3d
from uav_flight_core import OccupancyWorld, UAVController, UAVState


def look_at_from_state(state: UAVState, distance=0.8):
    cy, sy = math.cos(state.yaw), math.sin(state.yaw)
    cp, sp = math.cos(state.pitch), math.sin(state.pitch)
    forward = np.array([cy * cp, sy * cp, sp], dtype=np.float32)
    pos = np.array([state.x, state.y, state.z], dtype=np.float32)
    return pos + distance * forward


def load_optional_layer(data_dir: Path, name: str):
    path = data_dir / name
    return np.load(path) if path.exists() else None


def make_proxy_wind(world: OccupancyWorld, speed: float, direction_deg: float) -> np.ndarray:
    theta = math.radians(direction_deg)
    unit = np.array([math.cos(theta), math.sin(theta), 0.0], dtype=np.float32)
    z = np.arange(world.shape[2], dtype=np.float32)
    z_world = world.origin[2] + (z + 0.5) * world.voxel_size
    height = np.clip((z_world - 0.15) / 0.9, 0.25, 1.35)
    wind = np.zeros(tuple(world.shape) + (3,), dtype=np.float32)
    wind[..., 0] = unit[0] * speed * height[None, None, :]
    wind[..., 1] = unit[1] * speed * height[None, None, :]
    return wind


def path_metrics(world, path, clearance, risk, wind, airspeed):
    if len(path) < 2:
        return {"length": 0.0, "min_clearance": 0.0, "risk": 0.0, "time": 0.0, "crosswind": 0.0}
    steps = np.diff(path, axis=0)
    seg_len = np.linalg.norm(steps, axis=1)
    length = float(seg_len.sum())
    idx = np.asarray([world.world_to_grid(p) for p in path], dtype=np.int32)
    idx = np.clip(idx, 0, world.shape - 1)
    if clearance is not None:
        clear_vals = clearance[idx[:, 0], idx[:, 1], idx[:, 2]]
        min_clearance = float(np.min(clear_vals))
    else:
        min_clearance = float("nan")
    risk_sum = float(np.sum(risk[idx[:, 0], idx[:, 1], idx[:, 2]])) if risk is not None else 0.0
    crosswind = 0.0
    if wind is not None and len(steps):
        dirs = steps / np.maximum(seg_len[:, None], 1e-6)
        sample = idx[:-1]
        w = wind[sample[:, 0], sample[:, 1], sample[:, 2]]
        tail = np.sum(w * dirs, axis=1)
        cross = np.linalg.norm(w - tail[:, None] * dirs, axis=1)
        crosswind = float(np.sum(cross * seg_len))
    return {
        "length": length,
        "min_clearance": min_clearance,
        "risk": risk_sum,
        "time": length / max(float(airspeed), 1e-3),
        "crosswind": crosswind,
    }


def hide_scene_handle(handle):
    if handle is None:
        return
    try:
        handle.visible = False
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ply", default="/root/autodl-tmp/citygaussian_uav/data_block123_R/block123_R_viewer.ply")
    parser.add_argument("--data-dir", default="/root/autodl-tmp/citygaussian_uav/data_block123_R/navigation_splatnav_v2")
    parser.add_argument("--out-dir", default="/root/autodl-tmp/citygaussian_uav/interactive_logs_block123_R")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--z", type=float, default=0.40)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    world = OccupancyWorld(data_dir)
    clearance = load_optional_layer(data_dir, "clearance.npy")
    risk = load_optional_layer(data_dir, "soft_risk.npy")
    start = world.find_free_near(preferred=[-7.18, -2.06], z_world=args.z)
    init = UAVState(t=0.0, x=float(start[0]), y=float(start[1]), z=float(start[2]), yaw=math.radians(200), pitch=0.0)
    controller = UAVController(world, init, speed=0.045, vertical_speed=0.035, yaw_step_deg=5, pitch_step_deg=4)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    viewer = Viewer(
        model_paths=[args.ply], host=args.host, port=args.port, background_color=(0.0, 0.0, 0.0),
        image_format="jpeg", reorient="disable", sh_degree=3, enable_transform=False, show_cameras=False,
        cameras_json=None, vanilla_deformable=False, vanilla_gs4d=False, vanilla_gs2d=False, up=None,
        default_camera_position=[init.x, init.y, init.z], default_camera_look_at=look_at_from_state(init).tolist(),
        no_edit_panel=True, no_render_panel=False, gsplat=False, gsplat_aa=False,
        gsplat_v1_example=False, gsplat_v1_example_aa=False, seganygs=None,
        vanilla_seganygs=False, vanilla_mip=False, vanilla_pvg=False,
    )

    handles = {}
    planned = {"path": np.empty((0, 3), dtype=np.float32), "autopilot": None}
    goal_presets = {
        "Block 1 street": [-8.8, -2.2, 0.41],
        "Boundary": [-5.1, -3.8, 0.41],
        "Block 2 street": [-5.1, -5.4, 0.41],
        "Block 3 street": [0.0, -6.3, 0.41],
        "High street": [0.0, -6.3, 0.70],
        "Custom vector": [0.0, -6.3, 0.41],
    }

    def apply_camera_to_client(client, state):
        pos = np.array([state.x, state.y, state.z], dtype=np.float32)
        client.camera.position = pos
        client.camera.look_at = look_at_from_state(state)
        client.camera.up_direction = np.array([0.0, 0.0, 1.0], dtype=np.float32)

    def save_traj():
        path = out_dir / "interactive_trajectory.csv"
        controller.save_csv(path)
        return path

    def update_scene_marker(server, state):
        pos = np.array([state.x, state.y, state.z], dtype=np.float32)
        if "drone" not in handles:
            handles["drone"] = server.scene.add_icosphere("/uav/drone", radius=0.055, color=(255, 40, 40), position=pos)
            handles["path_points"] = server.scene.add_point_cloud(
                "/uav/manual_path", points=pos[None, :], colors=(255, 230, 0), point_size=0.035, point_shape="circle"
            )
        else:
            handles["drone"].position = pos
            pts = np.array([[s.x, s.y, s.z] for s in controller.history], dtype=np.float32)
            try:
                handles["path_points"].points = pts
            except Exception:
                pass

    def update_planned_path(server, path, color=(40, 180, 255)):
        if len(path) == 0:
            return
        colors = np.repeat(np.asarray(color, dtype=np.uint8)[None, :], len(path), axis=0)
        if "planned_path" not in handles:
            handles["planned_path"] = server.scene.add_point_cloud(
                "/uav/planned_path", points=path.astype(np.float32), colors=colors, point_size=0.055, point_shape="circle"
            )
        else:
            handles["planned_path"].points = path.astype(np.float32)
            try:
                handles["planned_path"].colors = colors
            except Exception:
                pass
        if "goal" not in handles:
            handles["goal"] = server.scene.add_icosphere("/uav/goal", radius=0.075, color=(40, 220, 90), position=path[-1])
        else:
            handles["goal"].position = path[-1]

    def setup_uav_tab(viewer_obj, server, tabs):
        update_scene_marker(server, controller.state)
        with server.gui.add_folder("UAV Control") as uav_folder:
            status = server.gui.add_markdown(
                f"UAV ready. Position=({controller.state.x:.2f}, {controller.state.y:.2f}, {controller.state.z:.2f})"
            )
            with server.gui.add_folder("Autonomous Flight") as autonomy_folder:
                mode = server.gui.add_dropdown(
                    "Planning mode",
                    ("No wind A*", "Wind-aware A*", "Wind + risk/clearance A*"),
                    initial_value="Wind + risk/clearance A*",
                )
                goal_name = server.gui.add_dropdown("Goal preset", tuple(goal_presets.keys()), initial_value="Block 3 street")
                goal_vec = server.gui.add_vector3("Custom goal XYZ", initial_value=tuple(goal_presets["Block 3 street"]), step=0.05)
                wind_speed = server.gui.add_slider("Wind speed", min=0.0, max=1.5, step=0.05, initial_value=0.45)
                wind_dir = server.gui.add_slider("Wind direction deg", min=0.0, max=360.0, step=5.0, initial_value=270.0)
                airspeed = server.gui.add_slider("Airspeed", min=0.1, max=1.2, step=0.05, initial_value=0.45)
                auto_speed = server.gui.add_slider("Autopilot speed", min=0.05, max=0.6, step=0.05, initial_value=0.25)
                paused = server.gui.add_checkbox("Autopilot paused", initial_value=True)
                btn_plan = server.gui.add_button("Plan A to B")
                btn_execute = server.gui.add_button("Execute")
                btn_step = server.gui.add_button("Step once")
                btn_pause = server.gui.add_button("Pause / manual takeover")
                btn_reset = server.gui.add_button("Reset flight / clear plan")

            with server.gui.add_folder("Presets") as presets_folder:
                btn_block1 = server.gui.add_button("Teleport: Block 1 Street")
                btn_boundary = server.gui.add_button("Teleport: Block Boundary")
                btn_block2 = server.gui.add_button("Teleport: Block 2 Street")
                btn_block3 = server.gui.add_button("Teleport: Block 3 Street")
                btn_high = server.gui.add_button("Teleport: Higher Street")
            with server.gui.add_folder("Move") as move_folder:
                btn_w = server.gui.add_button("W Forward")
                btn_s = server.gui.add_button("S Back")
                btn_a = server.gui.add_button("A Left")
                btn_d = server.gui.add_button("D Right")
                btn_q = server.gui.add_button("Q Down")
                btn_e = server.gui.add_button("E Up")
            with server.gui.add_folder("View") as view_folder:
                btn_left = server.gui.add_button("Yaw Left")
                btn_right = server.gui.add_button("Yaw Right")
                btn_up = server.gui.add_button("Pitch Up")
                btn_down = server.gui.add_button("Pitch Down")
                btn_save = server.gui.add_button("Save Trajectory")

            def show_state(prefix, state):
                msg = "blocked" if state.collision else "ok"
                grid = world.world_to_grid([state.x, state.y, state.z])
                status.content = (
                    f"{prefix}: {msg}. Position=({state.x:.2f}, {state.y:.2f}, {state.z:.2f}), "
                    f"grid=({grid[0]}, {grid[1]}, {grid[2]}), yaw={math.degrees(state.yaw):.1f}, "
                    f"pitch={math.degrees(state.pitch):.1f}"
                )

            def selected_goal():
                if goal_name.value == "Custom vector":
                    return np.asarray(goal_vec.value, dtype=np.float32)
                return np.asarray(goal_presets[goal_name.value], dtype=np.float32)

            def current_wind():
                if mode.value == "No wind A*":
                    return None
                return make_proxy_wind(world, float(wind_speed.value), float(wind_dir.value))

            def clear_planned_path():
                planned["path"] = np.empty((0, 3), dtype=np.float32)
                planned["autopilot"] = None
                hide_scene_handle(handles.get("planned_path"))
                hide_scene_handle(handles.get("goal"))

            def reset_to_initial(event):
                clear_planned_path()
                paused.value = True
                goal_name.value = "Block 3 street"
                goal_vec.value = tuple(goal_presets["Block 3 street"])
                controller.state = UAVState(
                    t=0.0,
                    x=float(init.x),
                    y=float(init.y),
                    z=float(init.z),
                    yaw=float(init.yaw),
                    pitch=float(init.pitch),
                    roll=0.0,
                    collision=False,
                    note="reset",
                )
                controller.history = [controller.state]
                apply_camera_to_client(event.client, controller.state)
                update_scene_marker(server, controller.state)
                status.content = (
                    "Reset done. Choose a goal preset or custom XYZ, then click Plan A to B. "
                    f"Position=({controller.state.x:.2f}, {controller.state.y:.2f}, {controller.state.z:.2f})"
                )

            @btn_plan.on_click
            def _(event):
                start_xyz = np.array([controller.state.x, controller.state.y, controller.state.z], dtype=np.float32)
                goal_xyz = selected_goal()
                wind = current_wind()
                plan_mode = "baseline" if mode.value == "No wind A*" else ("wind" if mode.value == "Wind-aware A*" else "risk")
                use_clearance = clearance if plan_mode == "risk" else None
                use_risk = risk if plan_mode == "risk" else None
                path, expanded = plan_3d(
                    world, start_xyz, goal_xyz, mode=plan_mode, wind=wind, risk=use_risk,
                    clearance=use_clearance, airspeed=float(airspeed.value)
                )
                planned["path"] = path.astype(np.float32)
                planned["autopilot"] = Autopilot(controller, planned["path"], speed=float(auto_speed.value)) if len(path) else None
                paused.value = True
                if len(path):
                    update_planned_path(server, planned["path"])
                    m = path_metrics(world, planned["path"], clearance, risk, wind, float(airspeed.value))
                    status.content = (
                        f"planned {mode.value}: {len(path)} waypoints, expanded={expanded}, "
                        f"length={m['length']:.2f}, min_clearance={m['min_clearance']:.2f}, "
                        f"risk={m['risk']:.1f}, crosswind={m['crosswind']:.2f}, eta={m['time']:.1f}s"
                    )
                else:
                    status.content = f"planning failed: expanded={expanded}. Try a higher goal or another preset."

            def autopilot_step(event, dt=0.18):
                auto = planned.get("autopilot")
                if auto is None or len(planned["path"]) == 0:
                    status.content = "No planned path. Click Plan A to B first."
                    return False
                auto.speed = float(auto_speed.value)
                state = auto.tick(dt=dt)
                apply_camera_to_client(event.client, state)
                update_scene_marker(server, state)
                show_state("autopilot", state)
                if not auto.active:
                    status.content += " | finished or paused"
                    return False
                return True

            @btn_execute.on_click
            def _(event):
                auto = planned.get("autopilot")
                if auto is None:
                    status.content = "No planned path. Click Plan A to B first."
                    return
                paused.value = False
                auto.paused = False
                for _ in range(600):
                    if paused.value:
                        auto.paused = True
                        status.content = "Autopilot paused. Manual control is active."
                        break
                    if not autopilot_step(event, dt=0.18):
                        break
                    time.sleep(0.025)

            @btn_step.on_click
            def _(event):
                paused.value = False
                auto = planned.get("autopilot")
                if auto is not None:
                    auto.paused = False
                autopilot_step(event, dt=0.25)
                paused.value = True

            @btn_pause.on_click
            def _(event):
                paused.value = True
                auto = planned.get("autopilot")
                if auto is not None:
                    auto.paused = True
                status.content = "Autopilot paused. Manual W/S/A/D/Q/E control is active."

            @btn_reset.on_click
            def _(event):
                reset_to_initial(event)

            def do_command(event, command):
                paused.value = True
                auto = planned.get("autopilot")
                if auto is not None:
                    auto.paused = True
                state = controller.step(command)
                apply_camera_to_client(event.client, state)
                update_scene_marker(server, state)
                show_state(command, state)

            def teleport(event, preferred, z_world, yaw_deg=20.0):
                paused.value = True
                p = world.find_free_near(preferred=preferred, z_world=z_world)
                controller.state = UAVState(
                    t=controller.state.t + 1.0, x=float(p[0]), y=float(p[1]), z=float(p[2]),
                    yaw=math.radians(yaw_deg), pitch=0.0, roll=0.0, collision=False, note="teleport"
                )
                controller.history.append(controller.state)
                apply_camera_to_client(event.client, controller.state)
                update_scene_marker(server, controller.state)
                show_state("teleport", controller.state)

            @btn_block1.on_click
            def _(event):
                teleport(event, preferred=[-7.18, -2.06], z_world=0.411, yaw_deg=28.0)

            @btn_boundary.on_click
            def _(event):
                teleport(event, preferred=[-5.1, -3.8], z_world=0.40, yaw_deg=200.0)

            @btn_block2.on_click
            def _(event):
                teleport(event, preferred=[-5.1, -5.4], z_world=0.40, yaw_deg=200.0)

            @btn_block3.on_click
            def _(event):
                teleport(event, preferred=[0.0, -6.3], z_world=0.40, yaw_deg=180.0)

            @btn_high.on_click
            def _(event):
                teleport(event, preferred=[0.0, -6.3], z_world=0.70, yaw_deg=180.0)

            for button, command in [
                (btn_w, "W"), (btn_s, "S"), (btn_a, "A"), (btn_d, "D"), (btn_q, "Q"), (btn_e, "E"),
                (btn_left, "LEFT"), (btn_right, "RIGHT"), (btn_up, "UP"), (btn_down, "DOWN"),
            ]:
                @button.on_click
                def _(event, command=command):
                    do_command(event, command)

            @btn_save.on_click
            def _(event):
                path = save_traj()
                status.content = f"Saved trajectory to `{path}` with {len(controller.history)} states."

            handles["gui_refs"] = [
                uav_folder, autonomy_folder, presets_folder, move_folder, view_folder,
                status, mode, goal_name, goal_vec, wind_speed, wind_dir, airspeed, auto_speed, paused,
                btn_plan, btn_execute, btn_step, btn_pause, btn_reset,
                btn_block1, btn_boundary, btn_block2, btn_block3, btn_high,
                btn_w, btn_s, btn_a, btn_d, btn_q, btn_e,
                btn_left, btn_right, btn_up, btn_down, btn_save,
            ]

    print(f"Starting CityGaussian-UAV autonomy viewer on {args.host}:{args.port}", flush=True)
    print(f"PLY: {args.ply}", flush=True)
    print(f"Occupancy data dir: {args.data_dir}", flush=True)
    print(f"Initial UAV state: {init}", flush=True)

    def safe_setup_uav_tab(viewer_obj, server, tabs):
        print("Configuring UAV autonomy GUI...", flush=True)
        try:
            setup_uav_tab(viewer_obj, server, tabs)
            print("UAV autonomy GUI configured.", flush=True)
        except Exception:
            print("Failed to configure UAV autonomy GUI:", flush=True)
            traceback.print_exc()
            with tabs.add_tab("UAV Control"):
                server.gui.add_markdown(
                    "UAV autonomy GUI failed to initialize. Check server log for traceback."
                )

    viewer.start(tab_config_fun=safe_setup_uav_tab)


if __name__ == "__main__":
    main()

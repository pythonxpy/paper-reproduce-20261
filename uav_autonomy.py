"""3D A* planning and kinematic waypoint tracking for the interactive UAV viewer."""
import heapq
import math
import numpy as np


def _neighbors():
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx or dy or dz:
                    v = np.array([dx, dy, dz], dtype=float)
                    yield dx, dy, dz, v / np.linalg.norm(v), float(np.linalg.norm(v))


def plan_3d(world, start, goal, mode="baseline", wind=None, risk=None, clearance=None, airspeed=0.45):
    free = ~world.occ
    start = np.asarray(start, dtype=np.float32)
    goal = np.asarray(goal, dtype=np.float32)
    start_xyz = world.find_free_near(start[:2], float(start[2]))
    goal_xyz = world.find_free_near(goal[:2], float(goal[2]))
    s = tuple(world.world_to_grid(start_xyz).tolist())
    g = tuple(world.world_to_grid(goal_xyz).tolist())
    shape, vox = world.shape, world.voxel_size
    queue, cost, parent, seen = [(0.0, 0.0, s)], {s: 0.0}, {}, set()
    expanded = 0
    while queue:
        _, current_cost, node = heapq.heappop(queue)
        if node in seen: continue
        seen.add(node); expanded += 1
        if node == g:
            path = [node]
            while path[-1] in parent:
                path.append(parent[path[-1]])
            path.reverse()
            return np.asarray([world.grid_to_world(p) for p in path]), expanded
        for dx, dy, dz, direction, length in _neighbors():
            q = (node[0]+dx, node[1]+dy, node[2]+dz)
            if min(q) < 0 or np.any(np.asarray(q) >= shape) or not free[q]: continue
            step = length * vox
            penalty = 0.0
            if clearance is not None: penalty += 0.08 / max(float(clearance[q]), 0.05)
            if mode != "baseline" and wind is not None:
                local = wind[q]; tail = float(np.dot(local, direction)); cross = float(np.linalg.norm(local-tail*direction))
                penalty += 0.35*max(0., -tail) + 0.2*cross
            if mode == "risk" and risk is not None: penalty += 0.6*float(risk[q])
            candidate = current_cost + step + penalty * step
            if candidate < cost.get(q, 1e18):
                cost[q], parent[q] = candidate, node
                h = float(np.linalg.norm(np.asarray(q)-np.asarray(g))*vox/max(airspeed, .05))
                heapq.heappush(queue, (candidate+h, candidate, q))
    return np.empty((0, 3)), expanded


class Autopilot:
    def __init__(self, controller, path, speed=0.18):
        self.controller, self.path, self.speed, self.index, self.paused = controller, path, speed, 1, False

    @property
    def active(self): return not self.paused and self.index < len(self.path)

    def tick(self, dt=0.05):
        if not self.active: return self.controller.state
        pos = np.array([self.controller.state.x, self.controller.state.y, self.controller.state.z])
        target = self.path[self.index]; delta = target-pos; distance = float(np.linalg.norm(delta))
        if distance < .03: self.index += 1; return self.controller.state
        step = delta / max(distance, 1e-6) * min(self.speed*dt, distance)
        candidate = pos + step
        if self.controller.world.is_occupied(candidate): self.paused = True; return self.controller.step("HOVER", dt)
        state = self.controller.state; yaw = math.atan2(step[1], step[0]); pitch = math.atan2(step[2], math.hypot(step[0], step[1]))
        self.controller.state = type(state)(t=state.t+dt, x=float(candidate[0]), y=float(candidate[1]), z=float(candidate[2]), yaw=yaw, pitch=pitch, roll=0., collision=False, note="autopilot")
        self.controller.history.append(self.controller.state)
        return self.controller.state

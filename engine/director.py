from engine.scene import Scene


scene = None


def set_scene(_scene: Scene) -> None:
    """
    Set the current scene to the given scene
    """
    global scene
    scene = _scene

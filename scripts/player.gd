extends CharacterBody2D

var speed := 260.0

func _ready():
    queue_redraw()

func _physics_process(_delta):
    var dir = Input.get_vector("move_left", "move_right", "move_up", "move_down")
    velocity = dir * speed
    move_and_slide()
    position.x = clamp(position.x, 40.0, 2200.0)
    position.y = clamp(position.y, 40.0, 1400.0)
    queue_redraw()

func _draw():
    draw_circle(Vector2.ZERO, 22, Color("#3b82f6"))
    draw_circle(Vector2(0,-5), 9, Color("#f2c6a0"))
    draw_rect(Rect2(-15,5,30,22), Color("#1e40af"), true)

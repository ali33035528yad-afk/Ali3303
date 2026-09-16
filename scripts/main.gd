extends Node2D

var world_size := Vector2(2200, 1400)

func _ready():
    queue_redraw()
    $UI/Chat.text_submitted.connect(_on_chat)

func _draw():
    draw_rect(Rect2(Vector2.ZERO, world_size), Color("#17202a"), true)
    for x in range(100, 2200, 300):
        draw_rect(Rect2(x, 0, 80, 1400), Color("#303943"), true)
        draw_line(Vector2(x+40,0), Vector2(x+40,1400), Color("#e8d36b"), 3)
    for y in range(100, 1400, 300):
        draw_rect(Rect2(0, y, 2200, 80), Color("#303943"), true)
        draw_line(Vector2(0,y+40), Vector2(2200,y+40), Color("#e8d36b"), 3)

    for bx in range(150, 2100, 300):
        for by in range(150, 1300, 300):
            draw_rect(Rect2(bx,by,190,150), Color("#59636e"), true)
            draw_rect(Rect2(bx+15,by+15,160,120), Color("#74808c"), true)

    draw_rect(Rect2(900,520,400,260), Color("#246b45"), true)
    for p in [Vector2(960,580),Vector2(1080,700),Vector2(1190,590),Vector2(1240,720)]:
        draw_circle(p, 25, Color("#1f8a4c"))

func _on_chat(text):
    if text.strip_edges() == "":
        return
    $UI/ChatLog.text += "\nشما: " + text
    $UI/Chat.clear()

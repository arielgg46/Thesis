(define (problem floor_tile_fsp_example_problem)
    (:domain floor-tile)
    (:requirements :typing)
    (:objects color1 color2 - color tile1 tile2 tile3 tile4 tile5 tile6 tile7 tile8 tile9 - tile robot1 - robot)
    (:init
        ; Row 1
        (right tile2 tile1) (right tile3 tile2)
        ; Row 2
        (right tile5 tile4) (right tile6 tile5)
        ; Row 3
        (right tile8 tile7) (right tile9 tile8)
        ; Column 1
        (up tile1 tile4) (up tile4 tile7)
        ; Column 2
        (up tile2 tile5) (up tile5 tile8)
        ; Column 3
        (up tile3 tile6) (up tile6 tile9)
        ; Robot 1
        (robot-at robot1 tile1) (robot-has robot1 color1)
        ; Available colors
        (available-color color1) (available-color color2))
    (:goal (and
        ; Direct translation of the goal's natural language description to predicates
        (painted tile1 color1) (painted tile2 color1) (painted tile3 color1)
        (painted tile4 color1) (painted tile5 color2) (painted tile6 color1)
        (painted tile7 color1) (painted tile8 color1) (painted tile9 color1)
    ))
)
(define (problem floor-tile_problem)
    (:domain floor-tile)
    (:requirements :strips :typing)
    (:objects 
        robot1 - robot tile1 tile2 tile3 tile4 tile5 tile6 tile7 tile8 tile9 tile10 tile11 tile12 tile13 tile14 tile15 tile16 tile17 tile18 tile19 tile20 tile21 tile22 tile23 tile24 tile25 tile26 tile27 tile28 - tile color1 color2 - color 
    )
    (:init
        ; Grid definition: rows
(painted tile1 color1) (painted tile2 color2) (painted tile3 color1) (painted tile4 color2)
(painted tile5 color2) (painted tile6 color1) (painted tile7 color2) (painted tile8 color1)
(painted tile9 color1) (painted tile10 color2) (painted tile11 color1) (painted tile12 color2)
(painted tile13 color2) (painted tile14 color1) (painted tile15 color2) (painted tile16 color1)
(painted tile17 color1) (painted tile18 color2) (painted tile19 color1) (painted tile20 color2)
(painted tile21 color2) (painted tile22 color1) (painted tile23 color2) (painted tile24 color1)
(painted tile25 color1) (painted tile26 color2) (painted tile27 color1) (painted tile28 color2))
    (:goal (and
        ; Direct translation of the goal's natural language description to predicates(painted tile1 color1) (painted tile2 color2) (painted tile3 color1) (painted tile4 color2)
(painted tile5 color2) (painted tile6 color1) (painted tile7 color2) (painted tile8 color1)
(painted tile9 color1) (painted tile10 color2) (painted tile11 color1) (painted tile12 color2)
(painted tile13 color2) (painted tile14 color1) (painted tile15 color2) (painted tile16 color1)
(painted tile17 color1) (painted tile18 color2) (painted tile19 color1) (painted tile20 color2)
(painted tile21 color2) (painted tile22 color1) (painted tile23 color2) (painted tile24 color1)
(painted tile25 color1) (painted tile26 color2) (painted tile27 color1) (painted tile28 color2)))
)
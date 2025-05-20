(define (problem floor-tile_problem)
    (:domain floor-tile)
    (:requirements :strips :typing)
    (:objects 
        robot1 robot2 robot3 - robot tile1 tile2 tile3 tile4 tile5 tile6 tile7 tile8 tile9 tile10 tile11 tile12 tile13 tile14 tile15 tile16 tile17 tile18 tile19 tile20 tile21 tile22 tile23 tile24 tile25 - tile color1 color2 color3 - color )


    (:init
        (painted tile1 color1) (painted tile2 color1) (painted tile3 color1) (painted tile4 color1) (painted tile5 color1)
            (painted tile6 color1) (painted tile7 color1) (painted tile8 color1) (painted tile9 color1) (painted tile10 color1)
            (painted tile11 color1) (painted tile12 color1) (painted tile13 color1) (painted tile14 color1) (painted tile15 color1)
            (painted tile16 color1) (painted tile17 color1) (painted tile18 color1) (painted tile19 color1) (painted tile20 color1)
            (painted tile21 color1) (painted tile22 color1) (painted tile23 color1) (painted tile24 color1) (painted tile25 color1))

    (:goal 
        (and(painted tile1 color1) (painted tile2 color1) (painted tile3 color1) (painted tile4 color1) (painted tile5 color1)
            (painted tile6 color1) (painted tile7 color1) (painted tile8 color1) (painted tile9 color1) (painted tile10 color1)
            (painted tile11 color1) (painted tile12 color1) (painted tile13 color1) (painted tile14 color1) (painted tile15 color1)
            (painted tile16 color1) (painted tile17 color1) (painted tile18 color1) (painted tile19 color1) (painted tile20 color1)
            (painted tile21 color1) (painted tile22 color1) (painted tile23 color1) (painted tile24 color1) (painted tile25 color1))))
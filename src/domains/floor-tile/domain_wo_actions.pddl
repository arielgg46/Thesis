(define (domain floor-tile)
  (:requirements :typing)
  (:types
    robot tile color - object
  )

  (:predicates
    (robot-at ?r - robot ?x - tile)
    (up ?x - tile ?y - tile)
    (right ?x - tile ?y - tile)
    (painted ?x - tile ?c - color)
    (robot-has ?r - robot ?c - color)
    (available-color ?c - color)
  )
)
(define (problem blocksworld_problem)
    (:domain blocksworld)
    (:requirements :strips)
    (:objects b1 b2 b3 b4)
    (:init 
        ; Arm state
(arm-empty)
        ; Tower 1 with 2 blocks
(on-table b1) (on b2 b1) (clear b2)
        ; Tower 2 with 2 blocks
(on-table b3) (on b4 b3) (clear b4)
    )
    (:goal (and
        ; Arm state
(arm-empty)
        ; Tower 1 with block from Tower 2 on top
(on-table b1) (on b4 b1) (clear b4)
        ; Tower 2 with block from Tower 1 on top
(on-table b3) (on b2 b3) (clear b2)
    ))
)
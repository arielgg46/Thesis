(define (problem evenly_distributed_to_holding_4_8)
    (:domain gripper)
    (:requirements :strips)
    (:objects room1 room2 room3 room4 ball1 ball2 ball3 ball4 ball5 ball6 ball7 ball8 gripper1 gripper2 gripper3 gripper4 gripper5)
    (:init
        ; 4 Rooms
        (room room1) (room room2) (room room3) (room room4)
        ; 8 Balls
        (ball ball1) (ball ball2) (ball ball3) (ball ball4)
        (ball ball5) (ball ball6) (ball ball7) (ball ball8)
        ; 5 Grippers
        (gripper gripper1) (gripper gripper2) (gripper gripper3) (gripper gripper4) (gripper gripper5)
        ; Equally distributed balls in rooms: 2 balls per room
        (at ball1 room1) (at ball2 room1)
        (at ball3 room2) (at ball4 room2)
        (at ball5 room3) (at ball6 room3)
        (at ball7 room4) (at ball8 room4)
        ; Grippers state: all free
        (free gripper1) (free gripper2) (free gripper3) (free gripper4) (free gripper5)
        ; Robot location
        (at-robby room1)
    )
    (:goal (and
        ; Direct translation of the goal's natural language description to predicates
        (carry ball1 gripper1) (carry ball2 gripper2) (carry ball3 gripper3) (carry ball4 gripper4) 
        (free gripper5)
    ))
)
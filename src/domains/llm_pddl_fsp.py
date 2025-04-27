
fsp_example={}

fsp_example["blocksworld"] = """You have 5 blocks. 
b2 is on top of b5. 
b5 is on top of b1. 
b1 is on top of b4. 
b3 is on top of b2. 
b4 is on the table. 
b3 is clear. 
Your arm is empty. 
Your goal is to move the blocks. 
b4 should be on top of b3. 
A plan for the example problem is: 
 Pick up b4, put down b1, unstack b1 from b4, pick up b5, put down b5, unstack b5 from b1, pick up b2, put down b2, unstack b2 from b5, pick up b3, put down b3, and stack b4 on top of b3."""

fsp_example["floor-tile"] = """You have 4 rows and 3 columns of unpainted floor tiles. 
tile_0-1 tile_0-2 tile_0-3 
tile_1-1 tile_1-2 tile_1-3 
tile_2-1 tile_2-2 tile_2-3 
tile_3-1 tile_3-2 tile_3-3 
You have 1 robot. 
Each robot can paint in color white. 
robot2 is at tile_2-2. 
robot1 is at tile_0-1. 
Your goal is to paint the grid in the following pattern: 
tile_1-1 is white; tile_1-2 is white; tile_1-3 is white. 
A plan for the example problem is: 
 Robot1 paints tile_1-1 white, moves right to tile_0-2, paints tile_1-2 white, moves right to tile_0-3, and paints tile_1-3 white."""

fsp_example["gripper"] = """You control 2 robots, each robot has a left gripper and a right gripper. 
There are 4 rooms and 6 balls. 
robot2 is in room3. robot1 is in room2. 
ball1 is in room3. ball2 is in room1. ball3 is in room3. ball4 is in room2. ball5 is in room4. ball6 is in room4. 
The robots' grippers are free. 
Your goal is to transport the balls to their destinations. 
ball1 should be in room4. 
ball2 should be in room1. 
ball3 should be in room1. 
ball4 should be in room2. 
ball5 should be in room1. 
ball6 should be in room1. 
A plan for the example problem is: 
 Robot2 picks up ball1 with its left gripper in room3. 
Robot2 picks up ball3 with its right gripper in room3. 
Robot2 moves from room3 to room1. 
Robot2 drops ball3 in room1 with its right gripper. 
Robot2 moves from room1 to room4. 
Robot2 picks up ball5 with its right gripper in room4. 
Robot2 drops ball1 in room4 with its left gripper. 
Robot2 picks up ball6 with its left gripper in room4. 
Robot2 moves from room4 to room1. 
Robot2 drops ball6 in room1 with its left gripper. 
Robot2 drops ball5 in room1 with its right gripper."""
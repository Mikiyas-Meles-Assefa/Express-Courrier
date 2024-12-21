from cmu_graphics import *
import random
from PIL import Image
import os, pathlib
import pygame

# PIL image import path handling
def openImage(fileName):
    # Opens an image file from the same directory as the script
    return Image.open(os.path.join(pathlib.Path(__file__).parent, fileName))


class Road:
    def __init__(self, app, startX, startY, endX, endY, width):
        # Initialize the road object with its start and end coordinates,
        # width, and orientation
        self.startX = startX
        self.startY = startY
        self.endX = endX
        self.endY = endY
        self.width = width

        # Determine if the road is vertical or horizontal
        if startX == endX:
            self.orientation = "vertical"
            self.skewLeft = 0  # No skew needed for vertical roads
        else:
            self.orientation = "horizontal"
            # Account for width to avoid gaps at road corners
            self.skewLeft = app.roadWidth / 2
    
    def isPlayerInRegion(self, px, py):
        # Check if a player's coordinates (px, py) are within the road's region
        if self.orientation == 'vertical':
            left = self.startX - self.width / 2
            right = self.startX + self.width / 2
            top = min(self.startY, self.endY)  # Top boundary
            bottom = max(self.startY, self.endY)  # Bottom boundary
        else:
            left = min(self.startX, self.endX) - self.skewLeft
            right = max(self.startX, self.endX) + self.skewLeft
            top = self.startY - self.width / 2
            bottom = self.startY + self.width / 2
        
        # Return whether the point is within the boundaries
        return left <= px <= right and top <= py <= bottom
    
    def draw(self, app):
        # Draw the road as a black line
        endX = max(self.startX, self.endX)  # Ensure correct horizontal direction
        startX = min(self.startX, self.endX)
        drawLine(
            startX - app.mapLeft - self.skewLeft, self.startY - app.mapTop,
            endX - app.mapLeft + self.skewLeft, self.endY - app.mapTop,
            lineWidth=self.width, fill="black"
        )
    
    def drawRoadLine(self, app):
        # Draw the road's center line as dashed white
        drawLine(
            self.startX - app.mapLeft, self.startY - app.mapTop,
            self.endX - app.mapLeft, self.endY - app.mapTop,
            dashes=True, fill="white"
        )
    
    def __repr__(self):
        # Represent the road by its start and end coordinates
        return (f"{self.startX}, {self.startY}, {self.endX}, {self.endY}")


class MiniMap(Road):
    scale = 8.5  # Scale factor for minimap dimensions

    def __init__(self, app, startX, startY, endX, endY, width):
        # Initialize the minimap road by scaling down the coordinates and width
        super().__init__(app, startX, startY, endX, endY, width)
        self.startX = startX / MiniMap.scale
        self.startY = startY / MiniMap.scale
        self.endX = endX / MiniMap.scale
        self.endY = endY / MiniMap.scale
        self.width = width / MiniMap.scale

    def draw(self, app):
        # Draw the minimap road
        endX = max(self.startX, self.endX)
        startX = min(self.startX, self.endX)
        padScale = 0.59166  # Padding to position the minimap on the screen
        drawLine(
            startX - self.skewLeft / MiniMap.scale,
            self.startY + padScale * app.height,
            endX + self.skewLeft / MiniMap.scale,
            self.endY + padScale * app.height,
            lineWidth=self.width, fill="black"
        )

        # Draw the player's position on the minimap
        drawCircle(
            (app.player1.px + app.mapLeft) / MiniMap.scale,
            (app.player1.py + app.mapTop) / MiniMap.scale + padScale * app.height,
            app.player1.playerRadius * 3 / MiniMap.scale, fill='red'
        )


class Player:
    def __init__(self, px, py, playerRadius):
        # Initialize the player's position and radius
        self.playerRadius = playerRadius
        self.px = px
        self.py = py

    @staticmethod
    def signum(n):
        # Returns the sign of a number (-1, 0, or 1)
        return -1 if n < 0 else 0 if n == 0 else 1

    def move(self, app, dx, dy):
        # Predict the player's next position
        nextPx = self.px + dx
        nextPy = self.py + dy

        # Check if the next position is within the road region
        if self.isInRoadRegion(
            app, nextPx + app.mapLeft + (self.playerRadius) * Player.signum(dx),
            nextPy + app.mapTop + (self.playerRadius) * Player.signum(dy)
        ):
            # Handle horizontal scrolling and edge detection
            if dx > 0 and nextPx > app.width - app.margin:  # Right edge
                if app.mapLeft + dx < app.mapWidth - app.width:
                    app.mapLeft += dx
                else:
                    app.mapLeft = app.mapWidth - app.width
                    self.px = nextPx
            elif dx < 0 and nextPx < app.margin:  # Left edge
                if app.mapLeft + dx > 0:
                    app.mapLeft += dx
                else:
                    app.mapLeft = 0
                    self.px = nextPx
            else:
                self.px = nextPx

            # Handle vertical scrolling and edge detection
            if dy > 0 and nextPy > app.height - app.margin:  # Bottom edge
                if app.mapTop + dy < app.mapHeight - app.height:
                    app.mapTop += dy
                else:
                    app.mapTop = app.mapHeight - app.height
                    self.py = nextPy
            elif dy < 0 and nextPy < app.margin:  # Top edge
                if app.mapTop + dy > 0:
                    app.mapTop += dy
                else:
                    app.mapTop = 0
                    self.py = nextPy
            else:
                self.py = nextPy

    def draw(self, app):
        # Draw the player at its current position
        drawImage('snoonu.png', self.px, self.py, align='center')

    def isInRoadRegion(self, app, px, py):
        # Check if the player is within any road region
        for road in app.roads:
            if road.isPlayerInRegion(px, py):
                return True
        return False


class Computer(Player):
    def draw(self, app):
        # Draw the computer-controlled player
        drawImage('talabat.png', self.px - app.mapLeft,
                  self.py - app.mapTop, align='center')

    def moveStep(self, app, startPoint, endPoint):
        # Extract global start and end points
        startX, startY = startPoint
        endX, endY = endPoint
        startX, startY = startX - app.mapLeft, startY - app.mapTop
        endX_local = endX  # Convert to local coordinates
        endY_local = endY

        # Move horizontally towards the target point
        if abs(self.px - endX_local) <= app.dx:
            self.px = endX_local
        elif endX_local > self.px:
            self.move(app, app.dx, 0)
        else:
            self.move(app, -app.dx, 0)

        # Move vertically towards the target point
        if abs(self.py - endY_local) <= app.dy:
            self.py = endY_local
        elif endY_local > self.py:
            self.move(app, 0, app.dy)
        else:
            self.move(app, 0, -app.dy)

    def move(self, app, dx, dy):
        # Predict and validate the next position
        nextPx = self.px + dx
        nextPy = self.py + dy

        # Check if the computer player stays within the road region
        if self.isInRoadRegion(
            app, nextPx + (self.playerRadius) * Player.signum(dx),
            nextPy + (self.playerRadius) * Player.signum(dy)
        ):
            self.px = nextPx
            self.py = nextPy

    
    
class House:
    NextID = 0  # Static ID tracker for houses
    height = 100  # House height
    width = 100  # House width

    def __init__(self, app, cx, cy):
        # Initialize the house attributes
        self.cx = cx  # Center x-coordinate
        self.cy = cy  # Center y-coordinate
        self.color = 'brown'  # Default color of the house
        self.request = False  # Indicates if the house has an active request
        self.ID = House.NextID  # Unique ID for the house
        self.locationWidth, self.locationHeight = app.locationIconHouseSize
        self.locationIcon = app.locationIconHouseUrl
        # Shortened variable for readability
        shortName = app.locationIconHouseSizeSmall
        self.locationWidthSmall, self.locationHeightSmall = shortName
        self.locationIconSmall = app.locationIconHouseUrlSmall

        House.NextID += 1  # Increment the ID for the next house

    def draw(self, app):
        # Draw the house on the map
        drawRect(
            self.cx - app.mapLeft, self.cy - app.mapTop,
            House.width, House.height, fill=self.color, align='center'
        )

    def miniMapDraw(self, app):
        # Draw the house on the minimap
        self.roadRegion(app)
        padScale = 0.59166  # Padding scale for positioning
        scale = 8.5  # Minimap scale
        drawRect(
            self.cx / scale, (self.cy / scale) + app.height * padScale,
            100 / scale, 100 / scale, fill=self.color, align='center'
        )
        if self.request:
            # Draw request marker on the minimap
            drawCircle(
                self.cx / scale, self.cy / scale + padScale * app.height,
                30 / scale, fill='red'
            )
            drawRect(
                self.roadLeft / scale,
                self.roadTop / scale + app.height * padScale,
                (self.roadRight - self.roadLeft) / scale,
                (self.roadBottom - self.roadTop) / scale,
                fill='cyan', opacity=70
            )
            drawImage(
                self.locationIconSmall,
                self.cx / scale - self.locationWidthSmall / (0.25 * scale),
                (self.roadTop + self.roadBottom) / (2 * scale) +
                app.height * padScale - self.locationHeightSmall / (0.25 * scale)
            )

    def roadRegion(self, app):
        # Calculate the road region nearest to the house
        nearestRoad = self.nearestRoadToHouse(app)
        if nearestRoad.orientation == 'vertical':
            self.roadLeft = nearestRoad.startX - app.roadWidth / 2
            self.roadRight = nearestRoad.startX + app.roadWidth / 2
            self.roadTop = self.cy - House.height / 2
            self.roadBottom = self.cy + House.height / 2
        else:
            self.roadLeft = self.cx - House.width / 2
            self.roadRight = self.cx + House.width / 2
            self.roadTop = nearestRoad.startY - app.roadWidth / 2
            self.roadBottom = nearestRoad.startY + app.roadWidth / 2

    def isPlayerHere(self, app, player):
        # Check if the player is within the house's road region
        return (
            self.roadLeft <= player.px + app.mapLeft <= self.roadRight and
            self.roadTop <= player.py + app.mapTop <= self.roadBottom
        )

    def drawRoadRegion(self, app):
        # Draw the road region around the house
        self.roadRegion(app)
        drawRect(
            self.roadLeft - app.mapLeft, self.roadTop - app.mapTop,
            self.roadRight - self.roadLeft, self.roadBottom - self.roadTop,
            fill='cyan', opacity=70
        )
        if self.request:
            avgX = (self.roadLeft + self.roadRight) / 2
            avgY = (self.roadTop + self.roadBottom) / 2
            drawImage(
                self.locationIcon,
                avgX - app.mapLeft - self.locationWidth / 2,
                avgY - app.mapTop - self.locationHeight / 2
            )

    def nearestRoadToHouse(self, app):
        # Find the nearest road to the house
        nearest = app.mapWidth
        for road in app.roads:
            top = min(road.startY, road.endY)
            bottom = max(road.endY, road.endY)
            left = min(road.startX, road.endX)
            right = max(road.startX, road.endX)
            if road.orientation == 'vertical' and top < self.cy < bottom:
                distance = abs(self.cx - road.startX)
            elif left < self.cx < right:
                distance = abs(self.cy - road.startY)
            if distance < nearest:
                nearestRoad = road
                nearest = distance
        return nearestRoad

    def destinationPoint(self, app):
        # Calculate the destination point for delivery
        self.roadRegion(app)
        avgX = (self.roadLeft + self.roadRight) / 2
        avgY = (self.roadBottom + self.roadTop) / 2
        return avgX, avgY

    def distance(self, other):
        # Calculate the Euclidean distance between two houses
        return ((self.cx - other.cx) ** 2 + (self.cy - other.cy) ** 2) ** 0.5

    def __eq__(self, other):
        # Compare two houses by their coordinates
        return self.cx == other.cx and self.cy == other.cy


class Shop(House):
    def __init__(self, app, cx, cy):
        # Initialize a shop, inheriting from House
        super().__init__(app, cx, cy)
        self.color = 'blue'  # Shop-specific color
        self.locationWidth, self.locationHeight = app.locationIconShopSize
        self.locationIcon = app.locationIconShopUrl
        smallSize = app.locationIconShopSizeSmall
        self.locationWidthSmall, self.locationHeightSmall = smallSize
        self.locationIconSmall = app.locationIconShopUrlSmall


# Utility function to calculate distance between two points
def distanceTuple(tuple1, tuple2):
    x1, y1 = tuple1
    x2, y2 = tuple2
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


# Function to initiate a new delivery
def startNewDelivery(app, previousShop, previousHouse):
    shops = [shop for shop in app.shops if shop != previousShop]
    houses = [house for house in app.houses if house != previousHouse]
    shop = random.choice(shops)
    house = random.choice(houses)
    shop.request = True
    house.request = True
    return shop, house



import copy

def fastestPathFromGraph(app):
    # Get the current house and shop involved in the delivery
    app.currentHouse, app.currentShop
    
    # Create a temporary copy of the graph to modify
    # without affecting the original
    tempGraph = copy.deepcopy(app.graph)
    
    # Define source and destination points for the path
    src = (app.player2.px, app.player2.py)  # Player's current position
    dest1 = app.currentShop.destinationPoint(app)  # Shop's delivery point
    dest2 = app.currentHouse.destinationPoint(app)  # House's delivery point

    # Update the graph to include direct connections to the player's location,
    # shop's destination, and house's destination
    for road in app.roads:
        for check in [src, dest1, dest2]:
             # Check if the point lies on the road region
            if road.isPlayerInRegion(*check): 
                # Add connections to the temporary graph for the road endpoints
                if check not in tempGraph:
                    tempGraph[check] = {}
                
                # Calculate and add distances from the
                # check point to the road's endpoints
                xDist = distanceTuple(check, (road.startX, road.startY))
                yDist = distanceTuple(check, (road.endX, road.endY))
                tempGraph[check][(road.startX, road.startY)] = xDist
                tempGraph[check][(road.endX, road.endY)] = yDist

                # Ensure road endpoints are also added as keys in the graph
                if (road.startX, road.startY) not in tempGraph:
                    tempGraph[(road.startX, road.startY)] = {}
                xDist2 = distanceTuple(check, (road.startX, road.startY))
                tempGraph[(road.startX, road.startY)][check] = xDist2

                if (road.endX, road.endY) not in tempGraph:
                    tempGraph[(road.endX, road.endY)] = {}
                yDist2 = distanceTuple(check, (road.endX, road.endY))
                tempGraph[(road.endX, road.endY)][check] = yDist2

    # Compute the shortest path from the player to the shop
    pathToShop = dijsktra(tempGraph, src, dest1)
    
    # Compute the shortest path from the shop to the house
    pathToHouse = dijsktra(tempGraph, dest1, dest2)

    # Return the paths as a tuple
    return (pathToShop, pathToHouse)





# This helper function from line 436 - 470 is slightly adapted from
# a youtube tutorial on shortest path algorithms
# I learned about the algorithm from this tutorial
# link: https://youtu.be/OrJ004Wid4o


from heapq import heappop, heappush
import sys

def dijsktra(graph, src, dest):
    # Representation of infinity for initial distances
    inf = sys.maxsize  
    # Initialize distances and predecessors for all nodes
    nodeData = {node: {'distance': inf, 'pred': []} for node in graph}
    # Distance to source is 0
    nodeData[src]['distance'] = 0
    # Track visited nodes
    visited = set()
    # Priority queue of (distance, node)
    minHeap = [(0, src)] 

    while minHeap:
        # Get the node with the smallest distance
        currentDist, currentNode = heappop(minHeap) 
        # Skip if already visited
        if currentNode in visited:
            continue
        visited.add(currentNode)

        # If destination is reached, return the full path
        if currentNode == dest:
            return nodeData[dest]['pred'] + [dest]

        # Process all neighbors of the current node
        for neighbor, weight in graph[currentNode].items():
            if neighbor not in visited:
                newDist = currentDist + weight  # Calculate the new distance
                # Update the shortest distance if a better path is found
                if newDist < nodeData[neighbor]['distance']:
                    nodeData[neighbor]['distance'] = newDist
                    currentPred = nodeData[currentNode]['pred']
                    nodeData[neighbor]['pred'] = currentPred + [currentNode]
                    # Push the neighbor into the heap
                    heappush(minHeap, (newDist, neighbor))  


def reset(app):
    # Initialize background images and positions
    app.bgImages = {}
    app.bgImagePositions = []

    # Define paths and positions for background images
    imagePaths = [
        # (file_path, x_position, y_position)
        ("background1.png", 76, 76),
        ("background2.png", 562, 76),
        ("background3.png", 985, 76),
        ("background4.png", 985, 1276),
        ("background5.png", 74, 548),
        ("background6.png", 564, 350),
        ("background7.png", 645, 350),
        ("background8.png", 422, 706),
        ("background9.png", 74, 942),
        ("background10.png", 561, 942),
        ("background11.png", 74, 1177),
        ("background12.png", 1405, 74),
        ("background13.png", 563, 1274),
        ("background20.png", 1089, 707),
        ("background14.png", 1405, 1175),
        ("background15.png", 1088, 350),
        ("background16.png", 722, 549),
        ("background17.png", 903, 629),
        ("background18.png", 1331, 550),
        ("background19.png", 1757, 550),
    ]

    # Load each background image and its position
    for index, (path, x, y) in enumerate(imagePaths):
        pilImage = openImage(path)  # Open image using helper function
        cmuImage = CMUImage(pilImage)  # Convert to CMU image format
        app.bgImages[f'background{index+1}'] = cmuImage
        app.bgImagePositions.append((x, y))
   
    # Initialize background music and sound effects
    pygame.mixer.init()
    pygame.mixer.music.load('bgMusic1.mp3')
    pygame.mixer.music.play(-1)
    app.computerFirstSound = pygame.mixer.Sound('computerfirst.mp3')
    app.goToShopSound = pygame.mixer.Sound('gotoshop.mp3')
    app.goToHouseSound = pygame.mixer.Sound('gotohouse.mp3')
    app.pickFirstSound = pygame.mixer.Sound('pickfirst.mp3')
    app.pickUpSound = pygame.mixer.Sound('tap.mp3')
    app.gameOverSound = pygame.mixer.Sound('gameover.mp3')
    app.gameWinSound = pygame.mixer.Sound('gamewin.mp3')

    # Reset player and game state variables
    app.value = 0
    app.counter = 0
    app.dx = 25  # Player horizontal movement step
    app.dy = 25  # Player vertical movement step
    app.width = 800
    app.height = 600
    app.mapWidth = 2000  # Map dimensions
    app.mapHeight = 1500
    app.playerRadius = 17.5
    app.showMiniMap = True
    app.AIMode = False
    app.player1 = Player(100, 20, app.playerRadius)  # Initialize player
    app.player2 = Computer(140, 30, app.playerRadius / 2)  # Initialize AI player

    # Map scrolling properties
    app.mapLeft, app.mapTop = 0, 0
    app.margin = 250  # margin for minimap
    app.cx, app.cy = app.width / 2, app.height / 2  # Center of the map

    # Game scaling factors
    app.smaller = min(app.mapWidth, app.mapHeight)
    app.roadWidth = app.smaller / 20

    # Reset game states
    app.computerPicked = False
    app.currentOrientation = []
    app.instructionTab = 1
    app.gameOver = False
    app.gameWin = False
    app.setMaxShapeCount(10**18)  # Prevent rendering limits
    app.currentScreen = 'menu'  # Start at the menu screen
    app.iAI = 1
    app.score = 0
    app.player2Score = 0
    app.timer = 20  # Timer for game rounds
    app.computerTimer = 15  # Timer for AI decisions
    app.newHighScore = False  # Track new high scores

    # Load icons and their sizes
    app.locationIconHouseUrl = "locationiconhouse.png"
    app.locationIconHouseSize = getImageSize(app.locationIconHouseUrl)
    app.locationIconHouseUrlSmall = "locationiconhousesmall.png"
    app.locationIconHouseSizeSmall = getImageSize(app.locationIconHouseUrlSmall)
    app.locationIconShopUrl = "locationiconshop.png"
    app.locationIconShopSize = getImageSize(app.locationIconShopUrl)
    app.locationIconShopUrlSmall = "locationiconshopsmall.png"
    app.locationIconShopSizeSmall = getImageSize(app.locationIconShopUrlSmall)

    # node definitions
    node1 = (684.2105263157895, 670)
    node2 = (1964.3684210526314, 37.5)
    node3 = (1368.421052631579, 511.71875)
    node4 = (1719.298245614035, 670)
    node5 = (37.5, 1140.625)
    node6 = (526.3157894736842, 1453.125)
    node7 = (526.3157894736842, 312.5)
    node8 = (684.2105263157895, 511.71875)
    node9 = (526.3157894736842, 742.1875)  
    node10 = (947.3684210526316, 1238.28125)  
    node11 = (1719.298245614035, 511.71875)  
    node12 = (37.5, 1463.125)   
    node13 = (37.5, 511.71875)   
    node14 = (526.3157894736842, 37.5)   
    node15 = (1947.3684210526314, 1140.625)  
    node16 = (1368.421052631579, 1453.125)  
    node17 = (1368.421052631579, 312.5)   
    node18 = (1052.6315789473683, 1238.28125)  
    node19 = (1947.3684210526314, 670)   
    node20 = (1368.421052631579, 742.1875)   
    node21 = (1947.3684210526314, 511.71875)  
    node22 = (1368.421052631579, 37.5)   
    node23 = (1719.298245614035, 742.1875)   
    node24 = (1368.421052631579, 906.25)   
    node25 = (526.3157894736842, 1238.28125)  
    node26 = (37.5, 37.5)   
    node27 = (1052.6315789473683, 511.71875)  
    node28 = (1964.3684210526314, 1463.125)   
    node29 = (866.6666666666666, 906.25)   
    node30 = (526.3157894736842, 1140.625)  
    node31 = (947.3684210526316, 312.5)   
    node32 = (947.3684210526316, 1453.125) 
    node33 = (37.5, 906.25) 
    node34 = (1368.421052631579, 1238.28125)  
    node35 = (526.3157894736842, 670)  
    node36 = (385.96491228070175, 742.1875)  
    node37 = (866.6666666666666, 1238.28125)  
    node38 = (947.3684210526316, 37.5) 
    node39 = (1052.6315789473683, 742.1875) 
    node40 = (866.6666666666666, 670)   
    node41 = (1368.421052631579, 1140.625)  
    node42 = (526.3157894736842, 511.71875)  
    node43 = (1947.3684210526314, 906.25)   
    node44 = (385.96491228070175, 906.25)  

    
    # Updated road map
    app.roadMap = [
        node26, node2, node28, node12, node26, node30, node25, node18,
        node27, node8, node1, node40, node29, node44, node36, node9,
        node35, node1, node5, node30, node13, node42, node35, node1,
        node6, node25, node34, node16, node43, node24, node41, node15,
        node34, node41, node42, node7, node31, node17, node3, node11,
        node21, node33, node44, node39, node23, node4, node19, node20,
        node11, node4, node11, node21, node22, node17, node14, node7,
        node31, node38, node29, node37, node10, node32
    ]

    app.nodes = set(app.roadMap)

    app.roads = []
    app.miniMap = []
    for i in range(len(app.roadMap) - 1):
        startX, startY = app.roadMap[i]
        endX, endY = app.roadMap[i + 1]
        if startX != endX and startY != endY:
            continue
        app.roads.append(Road(app, startX, startY, endX,
                              endY, app.roadWidth))
        app.miniMap.append(MiniMap(app, startX, startY, endX,
                                   endY, app.roadWidth))

    
    
    
    app.houses = []
    
    app.shops = []    
  
    
    
    app.housePositions = [176, 153, 383, 159, 162, 392, 393, 405, 169, 632, 217,
                          767, 610, 821, 488, 821, 167, 1359, 178, 1251, 202,
                          1003, 438, 1004, 375, 1251, 382, 1366, 608, 533, 933,
                          582, 1212, 426, 1454, 816, 1631, 824, 1837, 795, 1853,
                          1049, 1510, 1028, 1481, 1354, 1667, 1350, 1829, 1241,
                          1514, 187, 1767, 180, 1546, 373, 836, 180, 1061, 176,
                          1061, 176]
    for i in range(0, len(app.housePositions), 2):
        app.houses.append(House(app, app.housePositions[i],
                                app.housePositions[i+1]))     
    app.shopPositions = [620, 161, 1275, 170, 1802, 372, 1836, 584, 1603, 632,
                         1439, 629, 1188, 601, 360, 620, 734, 767, 799, 585,
                         954, 693, 950, 822, 756, 413, 980, 415, 680, 1341, 842,
                         1336, 1194, 1060, 1459, 1221, 1857, 1342, 1618, 1229]
    for i in range(0, len(app.shopPositions), 2):
        app.shops.append(Shop(app, app.shopPositions[i],
                              app.shopPositions[i+1]))
    
    
    app.currentShop, app.currentHouse = startNewDelivery(app, Shop(app, 0,0),
                                                         House(app, 0,0))

    
    app.graph = {
        node1: {node8: distanceTuple(node1, node8),
                node35: distanceTuple(node1, node35),
                node40: distanceTuple(node1, node40)},
        
        node2: {node22: distanceTuple(node2, node22),
                node21: distanceTuple(node2, node21)},
        node3: {node17: distanceTuple(node3, node17),
                node21: distanceTuple(node3, node21)},
        node4: {node19: distanceTuple(node4, node19),
                node11: distanceTuple(node4, node11),
                node23: distanceTuple(node4, node23)},
        node5: {node33: distanceTuple(node5, node33),
                node12: distanceTuple(node5, node12),
                node30: distanceTuple(node5, node30)},
        node6: {node12: distanceTuple(node6, node12),
                node32: distanceTuple(node6, node32),
                node25: distanceTuple(node6, node25)},
        node7: {node14: distanceTuple(node7, node14),
                node31: distanceTuple(node7, node31)},
        node8: {node1: distanceTuple(node8, node1),
                node27: distanceTuple(node8, node27)},
        node9: {node35: distanceTuple(node9, node35),
                node36: distanceTuple(node9, node36)},
        node10: {node37: distanceTuple(node10, node37),
                 node18: distanceTuple(node10, node18),
                 node32: distanceTuple(node10, node32)},
        node11: {node21: distanceTuple(node11, node21),
                 node4: distanceTuple(node11, node4),
                 node3: distanceTuple(node11, node3)},
        node12: {node6: distanceTuple(node12, node6),
                 node5: distanceTuple(node12, node5)},
        node13: {node26: distanceTuple(node13, node26),
                 node42: distanceTuple(node13, node42),
                 node33: distanceTuple(node13, node33)},
        node14: {node7: distanceTuple(node14, node7),
                 node26: distanceTuple(node14, node26),
                 node38: distanceTuple(node14, node38)},
        node15: {node28: distanceTuple(node15, node28),
                 node41: distanceTuple(node15, node41),
                 node43: distanceTuple(node15, node43)},
        node16: {node28: distanceTuple(node16, node28),
                 node32: distanceTuple(node16, node32),
                 node34: distanceTuple(node16, node34)},
        node17: {node22: distanceTuple(node17, node22),
                 node3: distanceTuple(node17, node3),
                 node31: distanceTuple(node17, node31)},
        node18: {node10: distanceTuple(node18, node10),
                 node34: distanceTuple(node18, node34),
                 node39: distanceTuple(node18, node39)},
        node19: {node43: distanceTuple(node19, node43),
                 node21: distanceTuple(node19, node21),
                 node4: distanceTuple(node19, node4)},
        node20: {node39: distanceTuple(node20, node39),
                 node23: distanceTuple(node20, node23)},
        node21: {node2: distanceTuple(node21, node2),
                 node11: distanceTuple(node21, node11),
                 node19: distanceTuple(node21, node19)},
        node22: {node2: distanceTuple(node22, node2),
                 node17: distanceTuple(node22, node17),
                 node38: distanceTuple(node22, node38)},
        node23: {node4: distanceTuple(node23, node4),
                 node20: distanceTuple(node23, node20)},
        node24: {node43: distanceTuple(node24, node43),
                 node41: distanceTuple(node24, node41)},
        node25: {node30: distanceTuple(node25, node30),
                 node37: distanceTuple(node25, node37)},
        node26: {node14: distanceTuple(node26, node14),
                 node13: distanceTuple(node26, node13)},
        node27: {node8: distanceTuple(node27, node8),
                 node39: distanceTuple(node27, node39)},
        node28: {node15: distanceTuple(node28, node15),
                 node16: distanceTuple(node28, node16)},
        node29: {node40: distanceTuple(node29, node40),
                 node44: distanceTuple(node29, node44),
                 node37: distanceTuple(node29, node37)},
        node30: {node25: distanceTuple(node30, node25),
                 node5: distanceTuple(node30, node5)},
        node31: {node7: distanceTuple(node31, node7),
                 node17: distanceTuple(node31, node17),
                 node38: distanceTuple(node31, node38)},
        node32: {node6: distanceTuple(node32, node6),
                 node10: distanceTuple(node32, node10),
                 node16: distanceTuple(node32, node16)},
        node33: {node44: distanceTuple(node33, node44),
                 node5: distanceTuple(node33, node5),
                 node13: distanceTuple(node33, node13)},
        node34: {node16: distanceTuple(node34, node16),
                 node18: distanceTuple(node34, node18),
                 node41: distanceTuple(node34, node41)},
        node35: {node1: distanceTuple(node35, node1),
                 node9: distanceTuple(node35, node9),
                 node42: distanceTuple(node35, node42)},
        node36: {node9: distanceTuple(node36, node9),
                 node44: distanceTuple(node36, node44)},
        node37: {node10: distanceTuple(node37, node10),
                 node25: distanceTuple(node37, node25),
                 node29: distanceTuple(node37, node29)},
        node38: {node14: distanceTuple(node38, node14),
                 node22: distanceTuple(node38, node22),
                 node31: distanceTuple(node38, node31)},
        node39: {node18: distanceTuple(node39, node18),
                 node27: distanceTuple(node39, node27),
                 node20: distanceTuple(node39, node20)},
        node40: {node1: distanceTuple(node40, node1),
                 node29: distanceTuple(node40, node29)},
        node41: {node15: distanceTuple(node41, node15),
                 node24: distanceTuple(node41, node24),
                 node34: distanceTuple(node41, node34)},
        node42: {node7: distanceTuple(node42, node7),
                 node13: distanceTuple(node42, node13),
                 node35: distanceTuple(node42, node35)},
        node43: {node15: distanceTuple(node43, node15),
                 node24: distanceTuple(node43, node24),
                 node19: distanceTuple(node43, node19)},
        node44: {node36: distanceTuple(node44, node36),
                 node33: distanceTuple(node44, node33),
                 node29: distanceTuple(node44, node29)},
    }
        
        
        
    app.fastestPathToShop, app.fastestPathToHouse = fastestPathFromGraph(app)

    
def onAppStart(app):
    app.highScore = 0
    reset(app)



def onStep(app): 
    # Ensure game updates only during active gameplay
    if not (app.gameOver or app.gameWin or 
            app.currentScreen == 'menu' or app.currentScreen == 'instructions'):    
        
        # Increment the game counter
        app.counter += 1
        
        # Check for game-over conditions
        if app.timer <= 0:
            app.gameOver = True
            app.gameOverSound.play()
        elif app.computerTimer == 0:
            app.gameWin = True
            app.gameWinSound.play()

        # Decrement timers every 30 steps
        if app.counter % 30 == 0:
            if app.AIMode:
                app.computerTimer -= 1
            
            app.timer -= 1

        # Handle AI movement towards the shop
        if app.AIMode and app.currentShop.request:
            start = (app.player2.px, app.player2.py)
            end = app.fastestPathToShop[app.iAI]
            app.player2.moveStep(app, start, end)
            
            # Check if AI has reached the current path node
            endX, endY = end
            if app.player2.px == endX and app.player2.py == endY:
                app.iAI += 1
                # If AI reaches the shop, update state
                if app.iAI == len(app.fastestPathToShop):
                    app.currentShop.request = False
                    app.computerPicked = True
                    app.iAI = 1

        # Handle AI movement towards the house after pickup
        elif app.AIMode and app.computerPicked:
            start = (app.player2.px, app.player2.py)
            end = app.fastestPathToHouse[app.iAI]
            app.player2.moveStep(app, start, end)
            
            # Check if AI has reached the current path node
            endX, endY = end
            if app.player2.px == endX and app.player2.py == endY:
                app.iAI += 1
                # If AI reaches the house, complete delivery
                if app.iAI == len(app.fastestPathToHouse):
                    app.currentHouse.request = False
                    app.player2Score += 1
                    
                    # Award extra time based on delivery distance
                    distance = app.currentHouse.distance(app.currentShop)
                    extra = distance // 200
                    app.computerTimer += extra
                    
                    # Start a new delivery request
                    x, y = startNewDelivery(app, app.currentShop,
                                            app.currentHouse)
                    app.currentShop, app.currentHouse = x, y
                    
                    # Recalculate paths for AI
                    x, y = fastestPathFromGraph(app)
                    app.fastestPathToShop, app.fastestPathToHouse = x, y

                    # Reset AI path index
                    app.iAI = 1

                    

def onKeyHold(app, keys):
    # Only process key holds during active gameplay
    if not (app.gameOver or app.gameWin):
        currentOrientation = set()
        currentRoads = []
        
        # Determine the player's current road and orientation
        for road in app.roads:
            if road.isPlayerInRegion(app.player1.px + app.mapLeft,
                                     app.player1.py + app.mapTop):
                currentOrientation.add(road.orientation)
                currentRoads += [str(road)]
        
        # Adjust movement speed based on road orientation
        if len(currentOrientation) == 2:
            dx = app.dx
            dy = app.dy
        elif 'horizontal' in currentOrientation:
            dx = app.dx
            dy = app.dy / 4
        elif 'vertical' in currentOrientation:
            dx = app.dx / 4
            dy = app.dy
                
        # Handle player movement based on key presses
        if 'right' in keys:
            app.player1.move(app, dx, 0)
        if 'left' in keys:
            app.player1.move(app, -dx, 0)
        if 'up' in keys:
            app.player1.move(app, 0, -dy)
        if 'down' in keys:
            app.player1.move(app, 0, dy)
    



def onKeyPress(app, key):
    # Process key presses if the game is not over
    if not app.gameOver:
        # Toggle mini map visibility
        if key in 'Mm':
            app.showMiniMap = not app.showMiniMap
        
        # Handle 'enter' key actions (delivery and shop-related events)
        if key == 'enter':
            # If the shop is requesting and player is at the shop, handle request
            if (app.currentShop.request and
            app.currentShop.isPlayerHere(app, app.player1)):
                app.currentShop.request = False
                app.computerPicked = False
                app.iAI = 1
                app.pickUpSound.play()
            # If the house is requesting and player is at the house,
            # handle delivery
            elif (not app.currentShop.request and
                  app.currentHouse.isPlayerHere(app, app.player1)
                  and not app.computerPicked):
                app.currentHouse.request = False
                app.score += 1
                if app.score > app.highScore:
                    app.highScore = app.score
                    app.newHighScore = True
                app.pickUpSound.play()
                distance = app.currentHouse.distance(app.currentShop)
                extra = distance // 150
                app.timer += extra
                # Start new delivery and update path
                x, y = startNewDelivery(app, app.currentShop, app.currentHouse)
                app.currentShop, app.currentHouse = x, y
                x, y = fastestPathFromGraph(app)
                app.fastestPathToShop, app.fastestPathToHouse = x, y
            # Handle case when computer has picked
            elif app.computerPicked:
                app.computerFirstSound.play()
            # Handle case when player is at house and computer hasn't picked
            elif (app.currentHouse.isPlayerHere(app, app.player1) and
                  not app.computerPicked):
                app.pickFirstSound.play()
            # Handle navigation sounds based on shop request status
            else:
                if app.currentShop.request:
                    app.goToShopSound.play()
                else:
                    app.goToHouseSound.play()

    # Handle instructions navigation
    if key in 'nN' and app.instructionTab < 3:
        app.instructionTab += 1
    elif key in 'pP' and app.instructionTab > 1:
        app.instructionTab -= 1

    # Restart the game when 'R' or 'r' is pressed
    if key in 'Rr':
        app.currentScreen = 'menu'
        reset(app)


def drawInstructions(app):
    drawRect(0, 0, app.width, app.height, fill='lightblue')
    drawLabel('Instructions', app.width / 2, 50, size=40, fill='black')

    if app.instructionTab == 1:
        # Tab 1: General Gameplay Instructions
        drawLabel('General Gameplay:', app.width / 2, 100, size=30,
                  fill='darkblue')
        drawLabel('1. Your goal is to deliver items as quickly as possible.',
                  app.width / 2, 150, size=20, fill='black')
        drawLabel('2. Use the minimap to navigate to the requested locations.',
                  app.width / 2, 190, size=20, fill='black')
        drawLabel('3. Blue location icon = Shop | Red location icon = House.',
                  app.width / 2, 230, size=20, fill='blue')
        msg4 = '4. Go to the shop first and press "Enter" to pick up an item.'

        drawLabel(msg4, app.width / 2, 270, size=20, fill='black')
        msg5 = '5. Then, go to the house and press "Enter" to deliver the item.'
        drawLabel(msg5, app.width / 2, 310, size=20, fill='black')
        drawLabel('page 1 of 3', app.width / 2,
                  app.height - 100, size=20, fill='black')
        drawLabel('Press "N" to go to the next page of instructions.',
                  app.width / 2,
                  app.height - 50, size=20, fill='black')

    elif app.instructionTab == 2:
        # Tab 2: Controls and Timer
        drawLabel('Controls & Timer:', app.width / 2, 100, size=30,
                  fill='darkblue')
        drawLabel('1. Toggle the minimap on/off by pressing "M".',
                  app.width / 2, 150, size=20, fill='black')
        drawLabel('2. Move the player using the arrow keys.',
                  app.width / 2, 190, size=20, fill='black')
        msg3 = '3. You get extra time for each delivery (based on the distance).'
        drawLabel(msg3, app.width / 2, 230, size=20, fill='black')
        drawLabel('page 2 of 3', app.width / 2,
                  app.height - 100, size=20, fill='black')
        msgBottom = 'Press "P" to go to the previous page \
        or "N" for the next page of instructions'
        drawLabel(msgBottom, app.width / 2, app.height - 50,
                  size=20, fill='black')

    elif app.instructionTab == 3:
        # Tab 3: Win/Lose Conditions
        drawLabel('Win/Lose Conditions:', app.width / 2, 100,
                  size=30, fill='darkblue')
        drawLabel('Regular Mode:', app.width / 2, 150, size=25, fill='darkred')
        msg1 = '1. Deliver as many items as possible before the timer runs out.'
        drawLabel(msg1, app.width / 2, 190, size=20, fill='black')
        drawLabel('2. The game ends when you run out of time.',
                  app.width / 2, 230, size=20, fill='black')

        drawLabel('Vs Computer Mode:', app.width / 2, 270, size=25,
                  fill='darkred')
        drawLabel('1. You win if the computer runs out of time before you.',
                  app.width / 2, 310, size=20, fill='black')
        drawLabel('2. The computer wins if you run out of time first.',
                  app.width / 2, 350, size=20, fill='black')
        drawLabel('3. Plan your routes and be faster than the computer!',
                  app.width / 2, 390, size=20, fill='black')
        drawLabel('page 3 of 3', app.width / 2,
                  app.height - 100, size=20, fill='black')
        msgBottom = 'Press "P" to go to the previous page \
        or "R" to go back to main menu'
        drawLabel(msgBottom, app.width / 2,
                  app.height - 50, size=20, fill='black')



def redrawAll(app): 
    # Check if current screen is 'menu'
    
    if app.currentScreen == 'menu':
        
        # Draw background image
        drawImage('bg.png', 0, 0)  
        # Overlay with opacity
        drawRect(0, 0, app.width, app.height, fill='skyblue', opacity=65)
         # Game title
        drawLabel('Express Courier', app.width / 2, 100, size=40, fill='black',
                  bold = True)
        
        # Draw buttons for starting game, vs computer, and instructions
        drawRect(app.width / 2 - 100, 200, 200, 50, fill='white')
        drawLabel('Start Game', app.width / 2, 225, size=20, fill='black')
        drawRect(app.width / 2 - 100, 300, 200, 50, fill='white')
        drawLabel('Vs Computer', app.width / 2, 325, size=20, fill='black')
        drawRect(app.width / 2 - 100, 400, 200, 50, fill='white')
        drawLabel('Instructions', app.width / 2, 425, size=20, fill='black')
    
    
    # Check if the current screen is 'instructions'
    elif app.currentScreen == 'instructions':
        drawInstructions(app)  
    
    
    else:
        # Draw the map with green background
        drawRect(0, 0, app.mapWidth, app.mapHeight, fill='green')
        
        # Draw background images with scrolling offsets
        for index, (x, y) in enumerate(app.bgImagePositions):
            imageKey = f'background{index+1}'
            if imageKey in app.bgImages:
                drawImage(app.bgImages[imageKey],
                          x - app.mapLeft, y - app.mapTop)

        # Draw roads and road lines
        for road in app.roads:
            road.draw(app)
            
        for road in app.roads:
            road.drawRoadLine(app)

        # Draw shops and houses if requested
        for shop in app.shops:
            if shop.request:
                shop.drawRoadRegion(app)
        for house in app.houses:
            if house.request:
                house.drawRoadRegion(app)
        
        # Draw the player and possibly the AI player
        app.player1.draw(app)
        if app.AIMode:
            app.player2.draw(app)

        # Draw mini map if enabled
        if app.showMiniMap:
            drawRect(0, app.height * 0.59166, 230, 175, fill='darkgreen')
            for miniRoad in app.miniMap:
                miniRoad.draw(app)
            for house in app.houses:
                house.miniMapDraw(app)
            for shop in app.shops:
                shop.miniMapDraw(app)


        # Draw the score and timer display
        drawRect(0, 530, 235, 70, fill='white')
        drawLabel(f"You: {app.score}  Timer: {app.timer}", 117.5, 550,
                  size=20, fill='black')
        if app.AIMode:
            drawLabel(f"Computer: {app.player2Score} Timer: {app.computerTimer}",
                      117.5, 580, size=20, fill='black')
        else:
            drawLabel(f"High score: {app.highScore}", 117.5, 580,
                      size=20, fill='black')


        # Handle game over screen
        if app.gameOver:

            # Translucent overlay
            drawRect(0, 0, app.width, app.height, fill='black', opacity=70)
            # Title
            drawLabel('Game Over', app.width / 2, app.height / 3,
                      size=40, fill='red')
            if app.newHighScore:
                 # New high score label
                drawLabel(f'New High Score: {app.highScore}',
                          app.width / 2, app.height / 3 + 50,
                          size=30, fill='white') 
            else:
                 # Score label
                drawLabel(f'Score: {app.score}', app.width / 2,
                          app.height / 3 + 50, size=30, fill='white') 
            
            
            # Play again and main menu buttons
            drawRect(app.width / 2 - 100, app.height / 2 - 30, 200,
                     50, fill='white')
            drawLabel('Play Again', app.width / 2, app.height / 2,
                      size=20, fill='black')
            drawRect(app.width / 2 - 100, app.height / 2 + 50, 200,
                     50, fill='white')
            drawLabel('Main Menu', app.width / 2, app.height / 2 + 80,
                      size=20, fill='black')

        # Handle game win screen
        if app.gameWin:
            # Translucent overlay for game win
            drawRect(0, 0, app.width, app.height, fill='lightgreen', opacity=80)
             # Title for win
            drawLabel('You Won!', app.width / 2, app.height / 3,
                      size=40, fill='gold', bold=True) 
            # Final score label
            drawLabel(f'Final Score: {app.score}', app.width / 2,
                      app.height / 3 + 50, size=30, fill='white')  
            # Play again and main menu buttons
            drawRect(app.width / 2 - 100, app.height / 2 - 30,
                     200, 50, fill='white')
            drawLabel('Play Again', app.width / 2, app.height / 2,
                      size=20, fill='black')
            drawRect(app.width / 2 - 100, app.height / 2 + 50, 200,
                     50, fill='white')
            drawLabel('Main Menu', app.width / 2, app.height / 2 + 80,
                      size=20, fill='black')





def onMousePress(app, mouseX, mouseY):
    if app.currentScreen == 'menu':
        if app.width / 2 - 100 <= mouseX <= app.width / 2 + 100:
            if 200 <= mouseY <= 250:
                reset(app)
                # Start regular game
                app.currentScreen = 'regular'  
            elif 300 <= mouseY <= 350:
                reset(app)
                # Start Vs Computer game
                app.currentScreen = 'vsComputer'  
                app.AIMode = True  
            elif 400 <= mouseY <= 450:
                app.currentScreen = 'instructions' 

    if app.gameOver:
        # "Play Again" button
        if app.width / 2 - 100 <= mouseX <= app.width / 2 + 100:
            if app.height / 2 - 30 <= mouseY <= app.height / 2 + 20:
                app.GameOver = False
                if app.AIMode:
                    reset(app)
                    # Start Vs Computer game
                    app.currentScreen = 'vsComputer'  
                    app.AIMode = True  
                else:
                    # Restart the game
                    reset(app)  
                    app.currentScreen = 'regular' 
            elif app.height / 2 + 50 <= mouseY <= app.height / 2 + 100:
                app.gameOver = False
                # Go to the main menu
                app.currentScreen = 'menu'  

    if app.gameWin:
        # "Play Again" button
        if app.width / 2 - 100 <= mouseX <= app.width / 2 + 100:
            if app.height / 2 - 30 <= mouseY <= app.height / 2 + 20:
                app.gameWin = False
                if app.AIMode:
                    reset(app)
                    # Restart Vs Computer game
                    app.currentScreen = 'vsComputer'  
                    app.AIMode = True
                else:
                    # Restart the regular game
                    reset(app)  
                
            # "Main Menu" button
            elif app.height / 2 + 50 <= mouseY <= app.height / 2 + 100:
                reset(app)
                app.gameWin = False
                 # Go to the main menu
                app.currentScreen = 'menu' 


runApp()






# copy right
# 1. I designed the background images on canva.com using graphics
#    elements from the website
# 2. The sounds I used are free for use (from https://pixabay.com/sound-effects)





import krpc
import random
import time
import sys
import numpy as np
import math


# Qvalues class
class QValues:
    def __init__(self, epsilon=1.0, gamma=0.99, alpha=0.025):
        # Value of Epsilon
        self.epsilon = epsilon
        # Gamma. tend vers 1 plus les actions lointaines seront valorisees ( cigale vs fourmis)
        self.gamma = gamma
        self.alpha = alpha

    def updateE(self, epsilon):
        if epsilon > 0.1:
            self.epsilon = epsilon - 0.01
            return self.epsilon
        else:
            return self.epsilon

    def initE(self):
        self.epsilon = 1.0
        return self.epsilon


# state class
class State:
    def __init__(self, altitude, speed, pitch, heading, roll,v_state = 0):
        self.altitude = altitude
        self.speed = speed
        self.pitch = pitch
        self.heading = heading
        self.roll = roll
        self.v_state = v_state

# Actions class
class Actions:
    def droite(vessel):
        vessel.control.yaw = 1  # D

    def gauche(vessel):
        vessel.control.yaw = -1  # Q

    def haut(vessel):
        vessel.control.pitch = -1  # Z

    def bas(vessel):
        vessel.control.pitch = 1  # S

    def nothing(vessel):
        pass

    def next(vessel):
        vessel.control.activate_next_stage()

import win32api
import win32con

def get_touch_points():
  """Gets the current touch points on the screen."""
  points = []
  for i in range(win32api.GetTouchPointsCount()):
    point = win32api.GetTouchPointInfo(i)
    points.append((point.x, point.y))
  return points

def main():
  """Gets the current touch points and prints them to the console."""
  points = get_touch_points()
  for point in points:
    print(point)

if __name__ == "__main__":
  main()
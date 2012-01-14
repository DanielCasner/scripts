#include "cv.h"
#include "cvaux.h"
#include "highgui.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

static const char * DOC = "\
Uses OpenCV Library to extract a perspective transformation warping matrix\n\
for an image by having the user select points.\n\
\n\
Usage:\n\
    perspective IMG\n\
\n\
Arguments:\n\
    IMG is the image file to use\n\
\n\
Author:\n\
    Daniel Casner <www.danielcasner.org>\n\
\n\
Version:\n\
    0.1\n\
";

static int selected = -1;
#define N_POINTS 4
#define MAT_SIZE 3
#define forEachPoint for(int p=0; p<N_POINTS; ++p)

double dist(const CvPoint2D32f& p1, const CvPoint2D32f& p2) {
  double dx = p1.x - p2.x;
  double dy = p1.y - p2.y;
  return sqrt(dx*dx + dy*dy);
}

void mouseCB(int event, int x, int y, int flags, void* param) {
  CvPoint2D32f* points = (CvPoint2D32f*)param;
  double minDist = 1e6, d;
  switch(event) {
  case CV_EVENT_LBUTTONDOWN:
    forEachPoint {
      d = dist(points[p], cvPoint2D32f(x, y));
      if(d < minDist) {
	selected = p;
	minDist = d;
      }
    }
    break;
  case CV_EVENT_MOUSEMOVE:
    // Just continue through to the end of the function
    break;
  case CV_EVENT_LBUTTONUP:
    selected = -1;
    break;
  default:
    return; // Don't move the point on other events
  }
  if(selected >= 0 && selected < N_POINTS) {
    points[selected].x = x;
    points[selected].y = y;
  }
}

int main(int argc, char** argv) {
  IplImage* image;
  if(argc == 1 || !strcmp(argv[1], "-h") || !strcmp(argv[1], "--help")) {
    printf(DOC);
    return 1;
  }
  image = cvLoadImage(argv[1]);

  CvPoint2D32f points[N_POINTS];
  CvPoint2D32f srcPts[N_POINTS];
  CvSize size = cvGetSize(image);
  IplImage* screen = cvCreateImage(size, 8, 3);
  
  points[0] = cvPoint2D32f(0.0, 0.0);
  points[1] = cvPoint2D32f(size.width, 0.0);
  points[2] = cvPoint2D32f(0.0, size.height);
  points[3] = cvPoint2D32f(size.width, size.height);
  memcpy(srcPts, points, sizeof(CvPoint2D32f)*N_POINTS);

  cvNamedWindow(argv[0], CV_WINDOW_AUTOSIZE);
  cvSetMouseCallback(argv[0], mouseCB, points);
  int key = 0xffffffff;
  while(key == 0xffffffff) {
    cvCopy(image, screen);
    forEachPoint {
      cvCircle(screen, cvPoint((int)points[p].x, (int)points[p].y), 4, cvScalar(0, 255, 0, 0), CV_FILLED);
    }
    cvShowImage(argv[0], screen);
    key = cvWaitKey(10);
  }

  CvMat* tfrm = cvCreateMat(MAT_SIZE, MAT_SIZE, CV_32FC1);
  cvGetPerspectiveTransform(points, srcPts, tfrm);
  cvWarpPerspective(image, screen, tfrm);
  cvShowImage(argv[0], screen);
  cvWaitKey(0);
  for(int i=0; i<MAT_SIZE; ++i) {
    for(int j=0; j<MAT_SIZE; ++j)
      printf("%f\t", cvmGet(tfrm, i, j));
    printf("\n");
  }
}

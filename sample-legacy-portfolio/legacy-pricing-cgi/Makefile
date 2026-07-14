# Hand-written Makefile - requires GCC 3.4 (legacy toolchain)
CXX = g++
CXXFLAGS = -O2 -Wall
TARGET = pricing.cgi

all: $(TARGET)

$(TARGET): pricing.cpp
	$(CXX) $(CXXFLAGS) -o $(TARGET) pricing.cpp

install: $(TARGET)
	scp $(TARGET) deploy@pricing01:/var/www/cgi-bin/pricing.cgi

clean:
	rm -f $(TARGET)

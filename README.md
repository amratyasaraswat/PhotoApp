# PhotoApp

## Overview

**PhotoApp** is a real-time computer vision project that allows users to apply image filters using hand gestures detected via webcam. Built with OpenCV and MediaPipe, it demonstrates gesture recognition and real-time image processing.

## Features

- Real-time hand gesture recognition using webcam feed
- Filter application based on detected gestures
- Modular design with reusable components

## Installation

```bash
git clone https://github.com/amratyasaraswat/PhotoApp.git
cd PhotoApp
pip install -r requirements.txt
```

## Usage

Run the main app:

```bash
python src/app.py
```

Ensure your webcam is connected and active. Perform hand gestures to trigger image filters.

## Project Structure

```
PhotoApp/
├── src/
│   ├── app.py
│   ├── filters.py
│   ├── gestures.py
│   ├── main_old.py
│   ├── minecraft_old.py
│   └── __init__.py
├── data/
│   └── block_data.csv
├── assets/
│   └── sample.jpg
├── tests/
│   └── test_app.py
├── requirements.txt
├── README.md
```

## License

This project is released under the MIT License.

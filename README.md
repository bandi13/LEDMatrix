# LEDMatrix
Project for streaming a movie/animation/image on WLED matrix display. The idea is to play The Matrix on the matrix display. The framerate isn't terribly great at 10FPS on a 48x48 pixel display but it is watchable. I think it is more limited by my wireless setup than anything. YMMV.

## Usage
Set up the WLED hardware. I have a 48x48 pixel display configured. Note that the larger the display, the slower the refresh rate.

The Python script has a few options:
- --loop - In case you have a short clip or GIF animation
- --preview - Have the host machine show a preview of what should be displayed

The script takes in a `filename` and optionally a `hostname` for your WLED board. I've renamed mine to be `wled.local`, but yours might have some random strings attached to the name.

# Support
If you found this project useful, consider supporting my work:
[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoff.ee/bandi13)

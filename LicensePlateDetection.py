import math
import sys
from pathlib import Path

from matplotlib import pyplot
from matplotlib.patches import Rectangle

# import our basic, light-weight png reader library
import imageIO.png


# this function reads an RGB color png file and returns width, height, as well as pixel arrays for r,g,b
def readRGBImageToSeparatePixelArrays(input_filename):
    image_reader = imageIO.png.Reader(filename=input_filename)
    # png reader gives us width and height, as well as RGB data in image_rows (a list of rows of RGB triplets)
    (image_width, image_height, rgb_image_rows, rgb_image_info) = image_reader.read()

    print("read image width={}, height={}".format(image_width, image_height))

    # pixel arrays are lists of lists, where each inner list stores one row of greyscale pixels
    pixel_array_r = []
    pixel_array_g = []
    pixel_array_b = []

    for row in rgb_image_rows:
        pixel_row_r = []
        pixel_row_g = []
        pixel_row_b = []
        r = 0
        g = 0
        b = 0
        for elem in range(len(row)):
            # RGB triplets are stored consecutively in image_rows
            if elem % 3 == 0:
                r = row[elem]
            elif elem % 3 == 1:
                g = row[elem]
            else:
                b = row[elem]
                pixel_row_r.append(r)
                pixel_row_g.append(g)
                pixel_row_b.append(b)

        pixel_array_r.append(pixel_row_r)
        pixel_array_g.append(pixel_row_g)
        pixel_array_b.append(pixel_row_b)

    return (image_width, image_height, pixel_array_r, pixel_array_g, pixel_array_b)


# a useful shortcut method to create a list of lists based array representation for an image, initialized with a value
def createInitializedGreyscalePixelArray(image_width, image_height, initValue=0):
    new_array = [[initValue for x in range(image_width)] for y in range(image_height)]
    return new_array


def main():
    command_line_arguments = sys.argv[1:]

    SHOW_DEBUG_FIGURES = True

    # Can test different photos
    input_filename = "numberplate1.png"

    if command_line_arguments != []:
        input_filename = command_line_arguments[0]
        SHOW_DEBUG_FIGURES = False

    output_path = Path("output_images")
    if not output_path.exists():
        # create output directory
        output_path.mkdir(parents=True, exist_ok=True)

    output_filename = output_path / Path(input_filename.replace(".png", "_output.png"))
    if len(command_line_arguments) == 2:
        output_filename = Path(command_line_arguments[1])

    # we read in the png file, and receive three pixel arrays for red, green and blue components, respectively
    # each pixel array contains 8 bit integer values between 0 and 255 encoding the color values
    (image_width, image_height, px_array_r, px_array_g, px_array_b) = readRGBImageToSeparatePixelArrays(input_filename)

    # setup the plots for intermediate results in a figure
    fig1, axs1 = pyplot.subplots(2, 2)

    # GREY SCALE
    px_array = createInitializedGreyscalePixelArray(image_width, image_height)
    old_min = 1000.0
    old_max = 0.0
    for i in range(len(px_array)):  # rows

        for j in range(len(px_array[i])):  # num in row
            r_value = float(px_array_r[i][j])
            g_value = float(px_array_g[i][j])
            b_value = float(px_array_b[i][j])
            g = 0.299 * r_value + 0.587 * g_value + 0.114 * b_value
            px_array[i][j] = g

            # old max/min for stretching
            if g > old_max:
                old_max = g
            if g < old_min:
                old_min = g

    # CONTRAST STRETCHING
    for i in range(len(px_array)):
        for j in range(len(px_array[i])):
            s_out = (px_array[i][j] - old_min) * (255.0 / (old_max - old_min))
            px_array[i][j] = s_out

    axs1[0, 0].set_title('Grey Scale')
    axs1[0, 0].imshow(px_array, cmap='gray')

    # HIGH CONTRAST STRUCTURES
    new_array = createInitializedGreyscalePixelArray(image_width, image_height)
    cs_old_min = 1000.0
    cs_old_max = 0.0

    for i in range(2, image_height - 2):
        for j in range(2, image_width - 2):

            num_list = [px_array[i - 2][j - 2], px_array[i - 2][j - 1], px_array[i - 2][j], px_array[i - 2][j + 1],
                        px_array[i - 2][j + 2],
                        px_array[i - 1][j - 2], px_array[i - 1][j - 1], px_array[i - 1][j], px_array[i - 1][j + 1],
                        px_array[i - 1][j + 2],
                        px_array[i][j - 2], px_array[i][j - 1], px_array[i][j], px_array[i][j + 1], px_array[i][j + 2],
                        px_array[i + 1][j - 2], px_array[i + 1][j - 1], px_array[i + 1][j], px_array[i + 1][j + 1],
                        px_array[i + 1][j + 2],
                        px_array[i + 2][j - 2], px_array[i + 2][j - 1], px_array[i + 2][j], px_array[i + 2][j + 1],
                        px_array[i + 2][j + 2]
                        ]
            n = len(num_list)
            mean = sum(num_list) / n
            var = sum((x - mean) ** 2 for x in num_list) / n
            deviation = var ** 0.5
            new_array[i][j] = deviation

            if deviation < cs_old_min:
                cs_old_min = deviation
            if deviation > cs_old_max:
                cs_old_max = deviation

    for i in range(2, image_height - 2):
        for j in range(2, image_width - 2):
            cs_out = (new_array[i][j] - cs_old_min) * (255.0 / (cs_old_max - cs_old_min))
            new_array[i][j] = cs_out

    axs1[0, 1].set_title('High Contrast Structures')
    axs1[0, 1].imshow(new_array, cmap='gray')

    # THRESHOLDING
    for i in range(len(new_array)):
        for j in range(len(new_array[i])):
            if new_array[i][j] >= 140:
                new_array[i][j] = 1
            else:
                new_array[i][j] = 0

    # DILATION & EROSION
    # dilation x3
    d1_array = createInitializedGreyscalePixelArray(image_width, image_height)
    for i in range(1, image_height - 1):
        for j in range(1, image_width - 1):

            num_list = [new_array[i - 1][j - 1], new_array[i - 1][j], new_array[i - 1][j + 1],
                        new_array[i][j - 1], new_array[i][j], new_array[i][j + 1],
                        new_array[i + 1][j - 1], new_array[i + 1][j], new_array[i + 1][j + 1]
                        ]
            if 1 in num_list:
                d1_array[i][j] = 1
            else:
                d1_array[i][j] = 0

    d2_array = createInitializedGreyscalePixelArray(image_width, image_height)
    for i in range(1, image_height - 1):
        for j in range(1, image_width - 1):

            num_list = [d1_array[i - 1][j - 1], d1_array[i - 1][j], d1_array[i - 1][j + 1],
                        d1_array[i][j - 1], d1_array[i][j], d1_array[i][j + 1],
                        d1_array[i + 1][j - 1], d1_array[i + 1][j], d1_array[i + 1][j + 1]
                        ]
            if 1 in num_list:
                d2_array[i][j] = 1
            else:
                d2_array[i][j] = 0

    d3_array = createInitializedGreyscalePixelArray(image_width, image_height)
    for i in range(1, image_height - 1):
        for j in range(1, image_width - 1):

            num_list = [d2_array[i - 1][j - 1], d2_array[i - 1][j], d2_array[i - 1][j + 1],
                        d2_array[i][j - 1], d2_array[i][j], d2_array[i][j + 1],
                        d2_array[i + 1][j - 1], d2_array[i + 1][j], d2_array[i + 1][j + 1]
                        ]
            if 1 in num_list:
                d3_array[i][j] = 1
            else:
                d3_array[i][j] = 0

    # erosion x3
    e1_array = createInitializedGreyscalePixelArray(image_width, image_height)
    for i in range(1, image_height - 1):
        for j in range(1, image_width - 1):

            num_list = [d3_array[i - 1][j - 1], d3_array[i - 1][j], d3_array[i - 1][j + 1],
                        d3_array[i][j - 1], d3_array[i][j], d3_array[i][j + 1],
                        d3_array[i + 1][j - 1], d3_array[i + 1][j], d3_array[i + 1][j + 1]
                        ]
            if 0 in num_list:
                e1_array[i][j] = 0
            else:
                e1_array[i][j] = 1

    e2_array = createInitializedGreyscalePixelArray(image_width, image_height)
    for i in range(1, image_height - 1):
        for j in range(1, image_width - 1):

            num_list = [e1_array[i - 1][j - 1], e1_array[i - 1][j], e1_array[i - 1][j + 1],
                        e1_array[i][j - 1], e1_array[i][j], e1_array[i][j + 1],
                        e1_array[i + 1][j - 1], e1_array[i + 1][j], e1_array[i + 1][j + 1]
                        ]
            if 0 in num_list:
                e2_array[i][j] = 0
            else:
                e2_array[i][j] = 1

    e3_array = createInitializedGreyscalePixelArray(image_width, image_height)
    for i in range(1, image_height - 1):
        for j in range(1, image_width - 1):

            num_list = [e2_array[i - 1][j - 1], e2_array[i - 1][j], e2_array[i - 1][j + 1],
                        e2_array[i][j - 1], e2_array[i][j], e2_array[i][j + 1],
                        e2_array[i + 1][j - 1], e2_array[i + 1][j], e2_array[i + 1][j + 1]
                        ]
            if 0 in num_list:
                e3_array[i][j] = 0
            else:
                e3_array[i][j] = 1

    axs1[1, 0].set_title('Binary Close')
    axs1[1, 0].imshow(e3_array, cmap='gray')

    # LARGEST CONNECTED COMPONENT
    image_array = e3_array
    visited = createInitializedGreyscalePixelArray(image_width, image_height)
    cc_array = createInitializedGreyscalePixelArray(image_width, image_height)
    components = {}

    current_label = 1
    px_count = 0
    for i in range(len(image_array)):
        for j in range(len(image_array[i])):
            if image_array[i][j] != 0 and visited[i][j] != 1:
                q = [[i, j]]
                while len(q) != 0:
                    coord = q.pop()
                    cc_array[coord[0]][coord[1]] = current_label
                    visited[coord[0]][coord[1]] = 1
                    px_count += 1

                    # check left pixel
                    if ((coord[1] - 1) >= 0) and (image_array[coord[0]][coord[1] - 1] != 0) and (
                            visited[coord[0]][coord[1] - 1] != 1):
                        q.insert(0, [coord[0], coord[1] - 1])
                        visited[coord[0]][coord[1] - 1] = 1
                    # check right pixel
                    if ((coord[1] + 1) < image_width) and (image_array[coord[0]][coord[1] + 1] != 0) and (
                            visited[coord[0]][coord[1] + 1] != 1):
                        q.insert(0, [coord[0], coord[1] + 1])
                        visited[coord[0]][coord[1] + 1] = 1
                    # check up pixel
                    if ((coord[0] - 1) >= 0) and (image_array[coord[0] - 1][coord[1]] != 0) and (
                            visited[coord[0] - 1][coord[1]] != 1):
                        q.insert(0, [coord[0] - 1, coord[1]])
                        visited[coord[0] - 1][coord[1]] = 1
                    # check down pixel
                    if ((coord[0] + 1) < image_height) and (image_array[coord[0] + 1][coord[1]] != 0) and (
                            visited[coord[0] + 1][coord[1]] != 1):
                        q.insert(0, [coord[0] + 1, coord[1]])
                        visited[coord[0] + 1][coord[1]] = 1
                components[current_label] = px_count
                current_label += 1
                px_count = 0

    # Is biggest component correct ratio?
    components[0] = 0
    loop = True
    while loop is True:
        largest_block = 0
        for block in components:
            if components[block] > components[largest_block]:
                largest_block = block

        # find bounding box
        min_y = image_height
        max_y = 0
        min_x = image_width
        max_x = 0
        for i in range(len(cc_array)):
            for j in range(len(cc_array[i])):
                if cc_array[i][j] == largest_block:
                    if i < min_y:
                        min_y = i
                    if i > max_y:
                        max_y = i
                    if j < min_x:
                        min_x = j
                    if j > max_x:
                        max_x = j
        Ratio = (max_x - min_x) / (max_y - min_y)
        if (Ratio >= 1.5) and (Ratio <= 5):
            loop = False
        else:
            del components[largest_block]

    # Draw a bounding box as a rectangle into the input image
    axs1[1, 1].set_title('Final image of detection')
    axs1[1, 1].imshow(px_array, cmap='gray')
    rect = Rectangle((min_x, min_y), max_x - min_x, max_y - min_y, linewidth=1,
                     edgecolor='g', facecolor='none')
    axs1[1, 1].add_patch(rect)

    # write the output image into output_filename, using the matplotlib savefig method
    extent = axs1[1, 1].get_window_extent().transformed(fig1.dpi_scale_trans.inverted())
    pyplot.savefig(output_filename, bbox_inches=extent, dpi=600)

    if SHOW_DEBUG_FIGURES:
        # plot the current figure
        pyplot.show()


if __name__ == "__main__":
    main()

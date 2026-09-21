from PIL import Image, ImageOps
from pathlib import Path
from os.path import isfile

def convert(path, scale=1):
    img = Image.open(path).convert("RGB")

    img = ImageOps.scale(img, scale)

    pixel_count = 0

    output = ""

    for y in range(img.height):
        for x in range(img.width):
            r, g, b = img.getpixel((x, y))

            # Convert 8-bit channels to 5-6-5 bits
            r_565 = (r >> 3) & 0x1F  # Keep top 5 bits
            g_565 = (g >> 2) & 0x3F  # Keep top 6 bits
            b_565 = (b >> 3) & 0x1F  # Keep top 5 bits
            
            # Pack them into a single 16-bit integer
            rgb565 = (r_565 << 11) | (g_565 << 5) | b_565

            output += f"0x{rgb565:04x}"

            if x != img.width - 1 or y != img.height - 1:
                output += ", "
                pixel_count += 1
                if pixel_count % 16 == 0:
                    output += "\n\t"

    return output

def listAnimationFolders(directory):
    items = Path(directory).iterdir()

    return [item for item in items if item.is_dir()]

def getImagesInAnimationDirectory(directory: Path, extension="png"):
    paths = []
    for i in range(255):
        path = directory.joinpath(f"{i}.{extension}")

        if not isfile(path):
            break

        paths.append(path)

    print(f"Found {i} images(s) in {directory.name}")
    return paths

if __name__ == "__main__":
    folders = listAnimationFolders("animations")

    with open("ESP32-TV/src/bitmaps.h", "w") as file:
        file.write("#include <Arduino.h>\n\n")
        
        for folder in folders:
            images = getImagesInAnimationDirectory(folder)

            name = folder.name

            for i, image in enumerate(images):
                output = "const uint16_t {name}_{index} [] PROGMEM = ".format(name=name, index=i)
                output += "{\n\t"
                
                output += convert(image)

                output += "\n};"

                file.write(output)

                file.write("\n\n")

            file.write(f"const uint16_t* const {name.upper()}[] PROGMEM = " + "{\n")

            for i in range(len(images)):
                file.write(f"\t{name}_{i}")

                if i != len(images) - 1:
                    file.write(",\n")

            file.write("\n};")
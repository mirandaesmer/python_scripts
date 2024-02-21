import os
import sys
from shutil import copy2

from PIL import Image, UnidentifiedImageError

VALID_IMAGE_EXTENSIONS = ['.png', '.jpeg', 'jpg']
SMALL_DIR_NAME = 'too_small'
CORRECT_DIR_NAME = 'correct_aspect_ratio'
LARGE_DIR_NAME = 'too_large'


def group_images_by_aspect_ratio(
		width: int = 1920,
		height: int = 1080,
		error_margin: float = .01
	) -> None:
	"""
	Creates COPIES of all images in the current directory and sorts them into
	3 subdirectories by aspect ratio
	
	- /SMALL_DIR_NAME -:> image is too small in either direction
	- /CORRECT_DIR_NAME -:> dimensions are within error margin of desired ratio
	- /SMALL_DIR_NAME -:> image too large in either direction, can be cropped
	
	NOTE: Only uses COPY operations in order to avoid file losses
	NOTE: Prioritizes safety (no file losses) over speed
	NOTE: Only tested thoroughly on Windows 10 OS
	
	:param width: width in pixel units
	:param height: height in pixel units
	:param error_margin: error margin as a percent of both width and height
	:return: None
	"""
	curr_dir = os.getcwd()
	target_subdir = None
	target_aspect_ratio = width / height
	error_floor = target_aspect_ratio - (target_aspect_ratio * error_margin)
	error_ceiling = target_aspect_ratio + (target_aspect_ratio * error_margin)
	
	all_subdir_names = [
		f for f in os.listdir(curr_dir)
		if os.path.isdir(os.path.join(curr_dir, f))
	]
	all_file_names = [
		f for f in os.listdir(curr_dir)
		if os.path.isfile(os.path.join(curr_dir, f))
	]
	image_file_names = filter(
		lambda x: os.path.splitext(x)[1] in VALID_IMAGE_EXTENSIONS,
		all_file_names
	)
	
	if not image_file_names:
		print(f'No compatible image files in {curr_dir}')
		return
	
	# Create subdirectories if they do not already exist
	for subdir in [SMALL_DIR_NAME, CORRECT_DIR_NAME, LARGE_DIR_NAME]:
		if subdir not in all_subdir_names:
			try:
				os.mkdir(os.path.join(curr_dir, subdir))
			except FileExistsError as e:
				print(f'{subdir} already exists in {curr_dir}: {type(e)} {e}')
			except FileNotFoundError as e:
				print(f'{curr_dir} not found: {type(e)} {e}')
			except OSError as e:
				print(f'OS Exception when creating {subdir}: {type(e)} {e}')
	
	for i in image_file_names:
		try:
			img_obj = Image.open(os.path.join(curr_dir, i))
			w, h = img_obj.size
			aspect_ratio = w / h
		except FileNotFoundError as e:
			print(f'File {i} not found: {type(e)} {e}')
		except UnidentifiedImageError as e:
			print(f'File {i} cannot be opened or identified: {type(e)} {e}')
		except (ValueError, TypeError) as e:
			print(f'Format or type error when opening {i}: {type(e)} {e}')
		else:
			
			if w == width and h == height:
				target_subdir = CORRECT_DIR_NAME
			elif w < width or h < height:
				target_subdir = SMALL_DIR_NAME
			elif error_floor < aspect_ratio < error_ceiling:
				target_subdir = CORRECT_DIR_NAME
			else:
				target_subdir = LARGE_DIR_NAME
				
		try:  # No move operations, only copy
			copy2(
				os.path.join(curr_dir, i),
				os.path.join(curr_dir, target_subdir)
			)
		except Exception as e:
			print(f'Exception when copying {i}: {type(e)} {e}')
		else:
			print(f'"{i}" successfully copied to {target_subdir}')
		
		
if __name__ == '__main__':
	args = sys.argv[1:]
	group_images_by_aspect_ratio(*args)

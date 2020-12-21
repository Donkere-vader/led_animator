from pygui import PyGui
import json
import os
import copy


class Animator:
    def __init__(self):
        # gui
        self.pygui = PyGui(__name__)
        self.pygui.set_globals(animator=self, len=len, enumerate=enumerate)
        self.showing_window = None

        # editor
        self.selected_frame = 0
        self.play = False

        # file
        self._play_speed = 1000  # ms before next frame
        self.animation = []
        self.matrix_dimensions = [0, 0]
        self.file_name = ""

    @property
    def play_speed(self):
        entry = self.showing_window.get_item("play_speed_entry")
        if entry is not None:
            ps = entry.val()
            try:
                self._play_speed = int(ps)
            except ValueError:
                pass
        return self._play_speed

    def start(self):
        self.open_file_window()

    def open(self, file_name):
        self.file_name = file_name
        json_obj = json.load(open(f"saved_animations/{file_name}.leda"))
        self.matrix_dimensions = json_obj['dimensions']
        self.animation = json_obj['animation']
        self._play_speed = json_obj['speed']

        self.selected_frame = 0
        self.open_window(self.pygui.construct("animator"))

    def open_file_window(self):
        self.file_name = ""
        files = [
            file[:-len(".leda")] for file in os.listdir(
                'saved_animations'
            ) if file.endswith(".leda")
        ]
        self.open_window(self.pygui.construct("open", files=files))

    def open_window(self, window):
        old_window = self.showing_window
        self.showing_window = window
        if old_window is not None:
            old_window.replace(self.showing_window)
        else:
            self.showing_window.show()

    def save(self):
        json_obj = {
            "speed": self.play_speed,
            "dimensions":  self.matrix_dimensions,
            "animation": self.animation
        }
        json.dump(
            json_obj,
            open(f'saved_animations/{self.file_name}.leda', 'w')
        )

    def open_new_file_window(self):
        self.file_name = ""
        self.open_window(self.pygui.construct('new'))

    def open_new_file(self):
        self.file_name = self.showing_window.get_item("file_name").val()
        try:
            self.matrix_dimensions = (
                int(self.showing_window.get_item("matrix_height").val()),
                int(self.showing_window.get_item("matrix_width").val())
            )
        except ValueError:
            self.pygui.message.showerror(
                "Invalid values",
                "Please only supply integers for width and height"
            )

        # set first frame
        self.animation = [
            [
                [0 for _1 in range(self.matrix_dimensions[0])]
                for _ in range(self.matrix_dimensions[1])
            ]
        ]

        self.save()
        self.open_window(self.pygui.construct('animator'))

    def pixel_pressed(self, x, y):
        button = self.showing_window.get_item(f"button_({x}:{y})")

        self.animation[self.selected_frame][y][x] = 1 if self.animation[
            self.selected_frame][y][x] == 0 else 0
        button.config(bg="white" if self.animation[
            self.selected_frame][y][x] == 1 else "black")

    def add_frame(self):
        self.animation.append(copy.deepcopy(self.animation[-1]))
        self.showing_window.reload("frames")
        # self.open_window(self.pygui.construct('animator'))

    def select_frame(self, frame):
        self.showing_window.get_item(
            f"frame_button_{self.selected_frame}"
        ).config(bg="white", fg="black")
        self.selected_frame = frame
        self.showing_window.get_item(
            f"frame_button_{self.selected_frame}"
        ).config(bg="black", fg="white")

        for y in range(self.matrix_dimensions[1]):
            for x in range(self.matrix_dimensions[0]):
                btn = self.showing_window.get_item(f"button_({x}:{y})")
                btn.config(
                    bg="black" if self.animation[
                        self.selected_frame][y][x] == 0 else "white"
                )

    def delete_frame(self):
        if len(self.animation) > 1:
            self.animation.remove(self.animation[self.selected_frame])
            self.selected_frame = max(self.selected_frame - 1, 0)
            self.showing_window.reload("frames")

    def update_frame(self):
        if not self.play:
            return
        f = self.selected_frame + 1
        if self.selected_frame == len(self.animation) - 1:
            f = 0
        self.select_frame(f)
        self.showing_window.after(self.play_speed, self.update_frame)

    def toggle_preview(self):
        self.play = not self.play
        btn = self.showing_window.get_item("toggle_preview_button")
        btn.config(
            bg="red" if self.play else "green",
            text="Pause" if self.play else "Play"
        )
        self.update_frame()

    def export(self):
        if self.file_name == "":
            return
        self.save()

        big_str = "".join(["".join([
            "".join([str(item) for item in row]) for row in frame]
            ) for frame in self.animation])
        num = int(big_str, 2)
        export = (len(self.animation), self.matrix_dimensions, num)
        self.open_window(self.pygui.construct("export", export=export))

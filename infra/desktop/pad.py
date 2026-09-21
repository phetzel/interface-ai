"""Native synthetic calibration fixture with an independent test oracle.

The oracle is only for this input smoke test. Future banking replay cannot use it.
"""

import tkinter as tk

from common import HEIGHT, STATE, WIDTH, write_json

root = tk.Tk()
root.title('interface-ai desktop calibration')
root.geometry(f'{WIDTH}x{HEIGHT}+0+0')
root.attributes('-fullscreen', True)
root.configure(bg='#f1f5f9')

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='#f1f5f9', highlightthickness=0)
canvas.place(x=0, y=0)
canvas.create_rectangle(0, 0, WIDTH, 104, fill='#0f172a', outline='')
canvas.create_text(
    64,
    42,
    text='interface-ai / desktop calibration',
    anchor='w',
    fill='white',
    font=('DejaVu Sans', 24, 'bold'),
)
canvas.create_text(
    64,
    78,
    text='Native input fixture · synthetic data only · 1280 × 800',
    anchor='w',
    fill='#94a3b8',
    font=('DejaVu Sans', 12),
)
canvas.create_text(
    64, 137, text='POINTER TARGETS', anchor='w', fill='#475569', font=('DejaVu Sans', 11, 'bold')
)

state = {'ready': False, 'clicks': [], 'submitted': '', 'scrollTop': 0.0}
target_boxes = []
for number, x, color in [(1, 80, '#2563eb'), (2, 300, '#7c3aed'), (3, 520, '#ea580c')]:
    rectangle = canvas.create_rectangle(x, 170, x + 160, 290, fill=color, outline='')
    target_boxes.append((number, x, rectangle))
    canvas.create_text(
        x + 80, 215, text=str(number), fill='white', font=('DejaVu Sans', 24, 'bold')
    )
    canvas.create_text(x + 80, 260, text='Click to verify', fill='white', font=('DejaVu Sans', 10))


def clicked(event):
    for number, x, rectangle in target_boxes:
        if x <= event.x <= x + 160 and 170 <= event.y <= 290:
            state['clicks'].append({'target': number, 'x': event.x_root, 'y': event.y_root})
            canvas.itemconfigure(rectangle, fill='#16a34a')


canvas.bind('<Button-1>', clicked)
canvas.create_text(
    64, 350, text='KEYBOARD INPUT', anchor='w', fill='#475569', font=('DejaVu Sans', 11, 'bold')
)
entry = tk.Entry(root, font=('DejaVu Sans', 18), relief='solid', borderwidth=1)
entry.place(x=80, y=380, width=530, height=50)
status = tk.Label(
    root,
    text='Waiting for input…',
    bg='#f1f5f9',
    fg='#475569',
    anchor='w',
    font=('DejaVu Sans', 16),
)
status.place(x=80, y=475, width=700, height=50)


def submit(_event=None):
    state['submitted'] = entry.get()
    status.configure(text=f'Received: {state["submitted"]}', fg='#15803d')


entry.bind('<Return>', submit)
tk.Button(root, text='Apply', command=submit, font=('DejaVu Sans', 14)).place(
    x=640, y=380, width=140, height=50
)
canvas.create_text(
    850, 137, text='SCROLL TEST', anchor='w', fill='#475569', font=('DejaVu Sans', 11, 'bold')
)
scroll = tk.Text(root, font=('DejaVu Sans Mono', 13), bg='white', relief='flat', wrap='none')
scroll.place(x=850, y=170, width=350, height=450)
scroll.insert('1.0', '\n'.join(f'Synthetic row {i:02d}' for i in range(1, 81)))
scroll.configure(state='disabled')
canvas.create_text(
    64,
    716,
    text='Observe in the operator panel. Calibration commands exercise desktop input.',
    anchor='w',
    fill='#475569',
    font=('DejaVu Sans', 12),
)
canvas.create_text(
    64,
    750,
    text='Use the operator app selector for bank workflows and goal discovery.',
    anchor='w',
    fill='#64748b',
    font=('DejaVu Sans', 11),
)


def publish():
    state['ready'] = root.winfo_viewable() == 1
    state['scrollTop'] = scroll.yview()[0]
    state['entry'] = entry.get()
    write_json(STATE, state)
    root.after(50, publish)


root.after(50, publish)
root.mainloop()

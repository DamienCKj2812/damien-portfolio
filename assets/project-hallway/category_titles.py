"""Human-readable titles for the two project-category portals."""
TITLES={'academic':'02 Academic Assignment Projects','personal':'03 Personal Projects'}


def refresh_category_titles(scene):
    for root in [obj for obj in scene.objects if obj.get('hallway_category_gate')]:
        body=TITLES[root['hallway_category_gate']]
        label=next(obj for obj in root.children if obj.type=='FONT' and obj.name.startswith('Category / number'))
        label.data.body=body.upper();label.data.size=.17
        scene.view_layers[0].update()
        width=max(point[0] for point in label.bound_box)-min(point[0] for point in label.bound_box)
        if width>3.20:
            label.data.size*=3.20/width
        root['hallway_category_title']=body
    scene.view_layers[0].update()

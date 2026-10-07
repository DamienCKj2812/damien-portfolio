import { MathUtils, Matrix4, Quaternion, Vector3 } from 'three'

export function createProjectCardFocus(project, alignment, size, exploring = false) {
  const { width, height } = size
  const mobile = width <= 600
  const short = height < 500
  const leftPanelWidth=Math.max(220,Math.min(320,width*.26-60))
  const rect = {
    left: !mobile && exploring ? Math.max(leftPanelWidth+60,width*.26) : mobile ? 32 : 100,
    right: width - (!mobile && exploring ? Math.min(320,width*.22) : mobile ? 24 : 38),
    top: short ? 76 : mobile ? exploring ? 218 : 170 : exploring ? 96 : width < 1100 ? 180 : 110,
    bottom: height - (short ? 72 : mobile ? exploring ? 330 : 220 : exploring ? 96 : 100),
  }
  // The native card includes its corner brackets; use authored bounds when
  // available, with a fallback for an already cached hallway package.
  const card = project.card || { center:[project.position[0],project.position[1],2.925], normal:[project.position[0]<0?1:-1,0,0], width:2.05, height:3.15 }
  const center = new Vector3().fromArray(card.center)
  const normal = new Vector3().fromArray(card.normal)
  const right = card.right ? new Vector3().fromArray(card.right) : new Vector3(0,0,1).cross(normal).normalize()
  const fov = 60, aspect = width / Math.max(1,height)
  const displayFov = Math.min(85, MathUtils.radToDeg(2*Math.atan(Math.tan(MathUtils.degToRad(fov)/2)*Math.max(1,1.6/aspect))))
  const tan = Math.tan(MathUtils.degToRad(displayFov)/2)
  const distance = Math.max(
    (card.height+.24)/(2*tan*Math.max(.1,(rect.bottom-rect.top)/height)),
    (card.width+.24)/(2*tan*aspect*Math.max(.1,(rect.right-rect.left)/width)),
  ) * 1.06 + (card.frontDepth || 0)
  const position = center.clone().addScaledVector(normal,distance).applyQuaternion(alignment.rotation).add(alignment.position)
  const worldCenter = center.clone().applyQuaternion(alignment.rotation).add(alignment.position)
  const quaternion = new Quaternion().setFromRotationMatrix(new Matrix4().lookAt(position,worldCenter,new Vector3(0,0,1))).normalize()
  const corners = [-1,1].flatMap(side => [-1,1].map(vertical => center.clone()
    .addScaledVector(right,side*(card.width/2+.08))
    .add(new Vector3(0,0,vertical*(card.height/2+.08)))
    .applyQuaternion(alignment.rotation).add(alignment.position)))
  return { position, quaternion, fov, displayFov, rect, corners,
    offsetX: width/2-(rect.left+rect.right)/2,
    offsetY: height/2-(rect.top+rect.bottom)/2 }
}

let mainsquare
let iFrame
let maxFrame=180
let maxSlices=32

let mySquare = class {
  constructor(level, x, y, flip, size, col) {
    this.level = level
    this.x = x
    this.y = y
    this.size = size
    this.flip = flip
    this.col=col
    if (this.level > 0) {
      var d = this.size << this.level
      this.sons = [new mySquare(this.level - 1, d, d, 1,this.size,this.col),
        new mySquare(this.level - 1, -d, -d, 1,this.size,this.col),
        new mySquare(this.level - 1, +d, -d, 0, this.size,this.col),
        new mySquare(this.level - 1, -d, +d, 0,this.size,this.col)
      ]
    }
  }

  update() {
    var f=iFrame/maxFrame
    translate(this.x, this.y)
    var s = (this.flip*2-1)
    rotate(PI * f*(1+this.level)*s/2)
    if (this.level > 0) {
      this.sons.forEach(c => c.update())
    } else {
      var c=f*this.col+(f+0.5)%1*(1-this.col)
      fill(255 * (this.flip*c+(1-this.flip)*(1-c)))
      strokeWeight(f*(1-f)*4)
      stroke(0)
      rect(-2*this.size, -2*this.size, this.size*4)
    }
    rotate(-PI * f*(1+this.level)*s/2)
    translate(-this.x, -this.y)
  }
}




function setup() {
  createCanvas(512, 512)
  mainSquare = [new mySquare(6, 0, 0, 0,3,0), new mySquare(3,0,0,0,16,1)]
  iFrame = 0
  frameRate(maxFrame/9)
}

function draw() {
  translate(256, 256)
  background(127)
  rotate(PI*iFrame/maxFrame/2)
  for(var i=0; i<maxSlices; i++) {
    a=2*PI/maxSlices*i
    b=2*PI/maxSlices*(i+1)
    fill(255*(i%2))
    triangle(0,0,512*cos(a),512*sin(a),512*cos(b),512*sin(b))
  }
  rotate(-PI*iFrame/maxFrame/2)
  mainSquare.forEach(c=>c.update())
  iFrame = (iFrame+1)%maxFrame
}
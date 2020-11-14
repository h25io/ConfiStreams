let squares = [];

let canvaSize = 515

let sqLen = canvaSize / 16;

let nbFrame = 180;

let iFrame = 0;

let delay = 50;




function setup() {
  createCanvas(canvaSize, canvaSize);

  for (let x = 0; x < 16; x++) {
    let line = []
    for (let y = 0; y < 16; y++) {
        line.push(new Square(sqLen * (x + 0.5), sqLen * (y + 0.5),sqLen,((x%2)^(y%2))));
    }
    squares.push(line);
  }

  for (let x = 0; x < 7; x++) {
    for (let y = 0; y < 7; y++) {
      if ((abs(x) % 2) ^ (abs(y) % 2)) {
        var t = random()<0.5?1:0
        squares[1+2*x][1+2*y].setTarget(0+t);
        squares[2+2*x][2+2*y].setTarget(2+t);
      }
    }
  }

  for (let i=1; i<16; i+=4) {
    squares[i+1][0].setTarget(2)
    squares[i][15].setTarget(0)
    squares[0][i+1].setTarget(3)
    squares[15][i].setTarget(1)
  }


}

function draw() {
  background(0);
  iFrame = frameCount % nbFrame;
  // iFrame=180;

  translate(width/2,height/2)
  scale(map(iFrame,0,nbFrame,2,1));
  // rotate(map(iFrame,0,nbFrame,0,PI))
  translate(-width/2,-height/2)

  squares.flatMap(l => l).forEach(function(s) {
    s.update()
  });
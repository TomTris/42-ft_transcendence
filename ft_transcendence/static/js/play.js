"use strict";

var camera, scene, renderer;
var mesh, sliderL, sliderR, table, ball, plate, trimU, trimD;

init();
// animate();

function init() {
  renderer = new THREE.WebGLRenderer({canvas: document.querySelector("#gameCanvas")});
  camera = new THREE.PerspectiveCamera(60, 1, 1, 1000);
  camera.position.z = 300;
  camera.position.y = -200;
  camera.rotation.x = 0.5;
  camera.aspect = 16/10;
  camera.updateProjectionMatrix();
  scene = new THREE.Scene();

  var width = (1000 - 80) / 2
  var height = 600 / 2
  var slder_width = 120 / 2

  var geometry = new THREE.DodecahedronGeometry(7, 4);
  var material = new THREE.MeshPhongMaterial({
    ambient: 0x555555,
    color: 0x555555,
    specular: 0xffffff,
    shininess: 30,
    shading: THREE.SmoothShading
  });
  ball = new THREE.Mesh(geometry, material);
  ball.castShadow = true;
  scene.add(ball);

  var geometry = new THREE.BoxGeometry(5, slder_width, 15);
  var material = new THREE.MeshPhongMaterial({
    ambient: 0x555555,
    color: 0xff0000,
    specular: 0xffffff,
    shininess: 2,
    shading: THREE.SmoothShading
  });
  sliderL = new THREE.Mesh(geometry, material);
  sliderL.position.x = - width / 2;
  scene.add(sliderL);

  var geometry = new THREE.BoxGeometry(5, slder_width, 15);
  var material = new THREE.MeshPhongMaterial({
    ambient: 0x555555,
    color: 0x0000ff,
    specular: 0xffffff,
    shininess: 2,
    shading: THREE.SmoothShading
  });
  sliderR = new THREE.Mesh(geometry, material);
  sliderR.position.x = width / 2;
  scene.add(sliderR);

  var geometry = new THREE.PlaneGeometry(2000, 2000);
  var material = new THREE.MeshPhongMaterial({
    ambient: 0xffffff,
    color: 0x9fff9f,
    specular: 0x000000,
    shininess: 0,
    shading: THREE.SmoothShading
  });
  plate = new THREE.Mesh(geometry, material);
  plate.position.z = -100;
  scene.add(plate);

  var geometry = new THREE.BoxGeometry(width, height, 10);
  var material = new THREE.MeshPhongMaterial({
    ambient: 0x000000,
    color: 0x00ff00,
    specular: 0x000000,
    shininess: 0,
    shading: THREE.SmoothShading
  });
  table = new THREE.Mesh(geometry, material);
  table.position.z = -10;
  scene.add(table);

  var geometry = new THREE.BoxGeometry(width, 5, 10);
  var material = new THREE.MeshPhongMaterial({
    ambient: 0xffffff,
    color: 0x8B4513,
    specular: 0x000000,
    shininess: 0,
    shading: THREE.SmoothShading
  });
  trimD = new THREE.Mesh(geometry, material);
  trimD.position.y = - height / 2;
  scene.add(trimD);

  var geometry = new THREE.BoxGeometry(width, 5, 10);
  var material = new THREE.MeshPhongMaterial({
    ambient: 0xffffff,
    color: 0x8B4513,
    specular: 0x000000,
    shininess: 0,
    shading: THREE.SmoothShading
  });
  trimU = new THREE.Mesh(geometry, material);
  trimU.position.y = height / 2;
  scene.add(trimU);



  var light1 = new THREE.PointLight(0xff7f7f, 1, 0);
  light1.position.set(200, 100, 300);
  light1.castShadow = true;
  scene.add(light1);

  var light2 = new THREE.PointLight(0x7f7fff, 1, 0);
  light2.position.set(-200, 100, 300);
  light2.castShadow = true;

  scene.add(light2);
  console.log("init");

}


function animate(px, py, p1, p2) {
  ball.position.x = px / 2 - 250;
  ball.position.y = -py / 2 + 150;
  sliderL.position.y = -p1 / 2 + 120;
  sliderR.position.y = -p2 / 2 + 120;
  renderer.render(scene, camera);
}

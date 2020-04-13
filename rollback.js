const fse = require('fs-extra');
const path = require('path');
const mime = require('mime');
const _ = require('lodash');

const root = 'D:\\Downloads\\Movies';

(async () => {
  let wrappers = await open(root);
  for (let wrapper of wrappers) {
    let src = wrapper.path;
    let dest = path.join(root, wrapper.meta.file_name);
    await fse.move(src, dest);
    console.log(src);
    console.log(dest);
    console.log(_.repeat('=', 120));
  }
})();

async function open(p) {
  let stat = await fse.stat(p);
  if (stat.isDirectory()) {
    let names = await fse.readdir(p);
    return names.reduce(async (prev, name) => {
      let file = path.join(p, name);
      let list = await open(file);
      return [...await prev, ...list];
    }, Promise.resolve([]));
  } else {
    let type = mime.getType(p);
    if (type.startsWith('video')) {
      let dir = path.dirname(p);
      let ext = path.extname(p);
      let base = path.basename(p, ext);
      let wrapper = {path: p, dir, base, ext};
      let m = path.join(dir, 'movie.json');
      if (await fse.pathExists(m))
        wrapper.meta = await fse.readJSON(m);
      return [wrapper];
    }
    return [];
  }
}

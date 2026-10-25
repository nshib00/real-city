// Выгрузка фактического TypeScript-каталога для документальной сверки.
const fs = require('fs')
const path = require('path')
const vm = require('vm')
const root = path.resolve(__dirname, '../..')
const ts = require(path.join(root, 'frontend/node_modules/typescript'))
const cache = new Map()

function load(filename) {
  const resolved = path.resolve(filename)
  if (cache.has(resolved)) return cache.get(resolved).exports
  const module = { exports: {} }
  cache.set(resolved, module)
  const source = fs.readFileSync(resolved, 'utf8')
  const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText
  const customRequire = (name) => {
    if (name.endsWith('.json')) return { default: JSON.parse(fs.readFileSync(path.resolve(path.dirname(resolved), name), 'utf8')) }
    return load(path.resolve(path.dirname(resolved), name + '.ts'))
  }
  vm.runInNewContext(code, { module, exports: module.exports, require: customRequire }, { filename: resolved })
  return module.exports
}

const catalogRoot = path.join(root, 'shared/catalog')
process.stdout.write(JSON.stringify({
  buildings: load(path.join(catalogRoot, 'buildings.ts')).buildingCatalog,
  resources: load(path.join(catalogRoot, 'resources.ts')).resourceCatalog,
}))

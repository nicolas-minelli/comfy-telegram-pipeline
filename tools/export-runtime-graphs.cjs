// Generate API graphs from the actual n8n request builders with synthetic job data.
// Does not run the scheduler prefix, submit prompts or contact n8n/Comfy/Telegram.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert/strict');
const root = path.resolve(__dirname, '..');
const workflow = JSON.parse(fs.readFileSync(path.join(root, 'workflows/ltx-generation.template.json'), 'utf8'));
const ltxTemplate = JSON.parse(fs.readFileSync(path.join(root, 'comfy/templates/ltx.json'), 'utf8'));
const output = path.join(root, 'comfy/api');
fs.mkdirSync(output, {recursive:true});

function build(name, marker, context) {
  const node = workflow.nodes.find(n => n.name === name);
  assert(node, 'Missing request builder: ' + name);
  const code = node.parameters.jsCode;
  assert.equal(code.split(marker).length, 2, 'Ambiguous/missing boundary: ' + name);
  const suffix = code.slice(code.indexOf(marker));
  const value = new vm.Script('(function(){\n' + suffix + '\n})()').runInNewContext(context, {timeout:1000});
  return JSON.parse(JSON.stringify(value[0].json));
}
function save(name, graph) {
  for (const node of Object.values(graph)) for (const v of Object.values(node.inputs || {})) {
    if (Array.isArray(v) && v.length === 2 && typeof v[0] === 'string' && Number.isInteger(v[1])) {
      assert(graph[v[0]], 'Missing graph link source: ' + v[0]);
    }
  }
  fs.writeFileSync(path.join(output, name), JSON.stringify(graph, null, 2) + '\n');
}

const requestId = 'tg-0-1';
const prefix = 'video/n8n/' + requestId;
const runId = requestId + '-e1';
const postPrefix = 'video/n8n/' + runId;
for (const aspect of ['9:16','16:9']) {
  const landscape = aspect === '16:9';
  const suffix = landscape ? '-16x9' : '';
  const request = {request_id:requestId, prompt:'Animate the supplied image with a subtle camera movement. Preserve the scene and subject. One continuous shot.',
    negative_prompt:'cuts, scene transitions, additional subjects, text, logos, watermark', duration_seconds:6, seed:1, aspect_ratio:aspect};
  const ltx = build('Build LTX Request', "const request = $('Prepare Request')", {
    $: name => ({first:()=>({json:name === 'Prepare Request' ? request : {name:'example-first-frame.png', type:'input', subfolder:''}})}),
    $input:{first:()=>({json:{template:ltxTemplate}})}
  }).prompt;
  assert.equal(ltx['403'].inputs.megapixels, 2);
  assert.equal(ltx['403'].inputs.aspect_ratio, landscape?'16:9 (Widescreen)':'9:16 (Portrait Widescreen)');
  save('ltx'+suffix+'.json', ltx);

  const stage = {interpolation_completed:true, interpolated_video:{windows_path:'E:/COMFY_OUTPUT/'+postPrefix+'/interpolation.mp4'},
    aspect_ratio:aspect, output_prefix:postPrefix, postprocess_run_id:runId, request_id:requestId};
  const up = build('Build Upscale Request', 'const stage = $input.first().json;', {
    $input:{first:()=>({json:stage})}
  }).upscale_request.prompt;
  assert.equal(up['5'].class_type, 'VHS_LoadVideoPath');
  assert.deepEqual(up['8'].inputs, {frames_per_batch:8});
  assert.deepEqual(up['17'].inputs.audio, ['5',2]);
  assert.equal(up['17'].inputs.frame_rate,60);
  assert.equal(up['900'].class_type,'N8NMoveFinalVideo');
  assert.equal(up['900'].inputs.final_basename,requestId);
  assert.equal(up['900'].inputs.run_id, requestId+'-e1');
  assert.equal(up['17'].inputs.filename_prefix, 'video/n8n/'+up['900'].inputs.run_id+'/upscale');
  assert.equal(up['15'].inputs.width,landscape?1920:1088);
  assert.equal(up['15'].inputs.height,landscape?1088:1920);
  save('upscale'+suffix+'.json',up);
}
const interpolation = build('Build Interpolation Request', "const job = $('Initialize Post Processing')", {
  $:name=>({first:()=>({json:{video:{relative_path:prefix+'/ltx.mp4'},output_prefix:postPrefix,postprocess_run_id:runId}})})
}).prompt;
assert.equal(interpolation['4'].inputs.file,prefix+'/ltx.mp4 [output]');
assert.equal(interpolation['16:9'].inputs.value,2);
assert.deepEqual(interpolation['16:5'].inputs.audio,['16:3',1]);
save('interpolation.json',interpolation);
console.log('Generated and checked 5 API graphs from installed-workflow builders; no external requests.');

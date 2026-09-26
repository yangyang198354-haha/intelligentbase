/**
 * @module MOD-IB-24（自检，非交付运行时）
 * @implements 验证 IFC-IB-259 的 SSE 分帧逻辑与后端 IFC-IB-225 编码的往返一致性
 * @author software-developer
 *
 * 离线自检：**真跑**前端 `parseSseStream`，而不是靠阅读代码断言「应该没问题」。
 *
 * ## 为什么值得单独跑这一块
 *
 * 前端里唯一有实质算法的地方就是 SSE 分帧，而它恰好是最难在浏览器里复现的一类缺陷：
 *   - 帧被 TCP 分片切断 → 半截 JSON → 「偶尔答到一半断掉」，刷新一次就好；
 *   - 多字节 UTF-8 被切在两块之间 → 出现 `�`；
 *   - 后端 `to_sse` 对空负载发 `data:`（无空格），对多行负载逐行加前缀 —— 解析端
 *     若用 `startsWith('data: ')`（带空格）就会**整帧丢失**，且丢的是正文。
 *
 * 因此本脚本把后端 `to_sse` 的编码规则**逐字复刻**为 `frame()`，再用前端解析器解回来，
 * 断言往返一致。这把「前后端两端各自都自认为对、拼起来却错」的风险压到离线可测。
 *
 * 运行：`node --experimental-strip-types src/scripts/sse_parser_selfcheck.mts`
 * （Node 24 可直接执行 TS：类型注解被擦除，无运行时开销；**不需要** npm install，
 * 故不触网。这也正是 `client.ts` 刻意避免参数属性等不可擦除语法的原因。）
 */
import { parseSseStream, type StreamEvent } from '../frontend/src/api/client.ts';

// 与后端 `ib/streaming/__init__.py: to_sse` 逐字对应（含空负载的 `data:` 无空格分支）
function frame(kind: string, payload: string | null = null): string {
  const lines = [`event: ${kind}`];
  const data = payload ?? '';
  if (data === '') {
    lines.push('data:');
  } else {
    for (const line of data.split('\n')) lines.push(`data: ${line}`);
  }
  return lines.join('\n') + '\n\n';
}

function toStream(text: string, chunkSize: number): ReadableStream<Uint8Array> {
  const bytes = new TextEncoder().encode(text);
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (let i = 0; i < bytes.length; i += chunkSize) {
        controller.enqueue(bytes.slice(i, i + chunkSize));
      }
      controller.close();
    },
  });
}

async function collect(stream: ReadableStream<Uint8Array>): Promise<StreamEvent[]> {
  const out: StreamEvent[] = [];
  for await (const event of parseSseStream(stream)) out.push(event);
  return out;
}

let failures = 0;

function check(name: string, ok: boolean, detail = ''): void {
  if (ok) {
    console.log(`PASS  ${name}`);
  } else {
    failures += 1;
    console.log(`FAIL  ${name}  ${detail}`);
  }
}

// ── 1. 单帧 ────────────────────────────────────────────────────────────
{
  const wire = frame('content', '你好，世界');
  const events = await collect(toStream(wire, 4096));
  check(
    'single_frame',
    events.length === 1 && events[0].kind === 'content' && events[0].data === '你好，世界',
    JSON.stringify(events),
  );
}

// ── 2. 空负载帧（`data:` 无空格 —— 后端 `done` 事件就是这个形状）────────
{
  const wire = frame('done');
  const events = await collect(toStream(wire, 4096));
  check(
    'empty_payload_frame',
    events.length === 1 && events[0].kind === 'done' && events[0].data === '',
    JSON.stringify(events),
  );
}

// ── 3. 跨 chunk 切断：每 1 字节喂一次（最恶劣分片）────────────────────
{
  const wire = frame('content', '流式内容') + frame('done');
  const events = await collect(toStream(wire, 1));
  check(
    'one_byte_chunks',
    events.length === 2 && events[0].data === '流式内容' && events[1].kind === 'done',
    JSON.stringify(events),
  );
}

// ── 4. 多字节 UTF-8 被切在两块之间（3 字节的汉字逐字节切）────────────
//     这正是 TextDecoder({stream:true}) 存在的理由；不用它就会出现「锟斤拷」类乱码。
{
  const wire = frame('content', '中文测试');
  const events = await collect(toStream(wire, 1));
  check('utf8_split_across_chunks', events.length === 1 && events[0].data === '中文测试', JSON.stringify(events));
}

// ── 5. 多行负载 + 行首空格（往返无损性）──────────────────────────────
{
  const payload = '第一行\n 缩进行\n尾行';
  const wire = frame('content', payload);
  const events = await collect(toStream(wire, 3));
  check('multiline_leading_space_roundtrip', events.length === 1 && events[0].data === payload, JSON.stringify(events));
}

// ── 6. CRLF 分隔（代理可能改写换行）──────────────────────────────────
{
  const wire = frame('content', 'crlf 正文').replace(/\n/g, '\r\n');
  const events = await collect(toStream(wire, 4096));
  check('crlf_frames', events.length === 1 && events[0].data === 'crlf 正文', JSON.stringify(events));
}

// ── 7. 注释/心跳行被忽略，不产生事件 ────────────────────────────────
{
  const wire = ': keep-alive\n\n' + frame('content', '有正文');
  const events = await collect(toStream(wire, 7));
  check('comment_ignored', events.length === 1 && events[0].data === '有正文', JSON.stringify(events));
}

// ── 8. degraded 事件负载是 JSON（前端据此显示降级横幅）──────────────
{
  const payload = JSON.stringify({ reason: 'vectorstore_unavailable', hint: '当前未接入知识资料库，以下回答基于通用知识。' });
  const wire = frame('reasoning', '正在分析问题…') + frame('degraded', payload) + frame('content', '答案') + frame('done');
  const events = await collect(toStream(wire, 5));
  const degraded = events.find((e) => e.kind === 'degraded');
  const parsed = degraded ? JSON.parse(degraded.data) : null;
  check(
    'degraded_json_payload',
    events.map((e) => e.kind).join(',') === 'reasoning,degraded,content,done' &&
      parsed?.hint === '当前未接入知识资料库，以下回答基于通用知识。',
    JSON.stringify(events),
  );
}

// ── 9. 尾部无空行的残帧也要吐出来（服务端异常中止时）────────────────
{
  const wire = frame('content', '完整帧') + 'event: content\ndata: 残';
  const events = await collect(toStream(wire, 64));
  check(
    'trailing_partial_frame_flushed',
    events.length === 2 && events[1].data === '残',
    JSON.stringify(events),
  );
}

console.log(failures === 0 ? '\nSSE parser selfcheck: ALL PASS' : `\nSSE parser selfcheck: ${failures} FAILED`);
process.exit(failures === 0 ? 0 : 1);

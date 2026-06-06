import { useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import { useSiteBehavior } from './effects'
import ParticleField from './ParticleField'
import {
  IcSensor, IcKafka, IcSpark, IcModel, IcAlert, IcStorage, IcMonitor,
  IcLogo, IcGithub, IcArrow,
} from './icons'

const REPO = 'https://github.com/yassnemo/iot-data-and-anomaly-detection-ml-system'
const USER = 'https://github.com/yassnemo'

const stagger = (i: number) => ({ ['--i']: i } as CSSProperties)

const NAV_LINKS = [
  ['#challenge', 'Challenge'],
  ['#architecture', 'Architecture'],
  ['#pipeline', 'Pipeline'],
  ['#model', 'The Model'],
  ['#results', 'Results'],
  ['#stack', 'Stack'],
] as const

export default function App() {
  const { stuck, active, progressRef } = useSiteBehavior()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="app">
      <div className="scroll-progress" ref={progressRef} aria-hidden="true" />

      {/* ===================== NAV ===================== */}
      <header className={`nav${stuck ? ' is-stuck' : ''}${menuOpen ? ' is-open' : ''}`}>
        <div className="nav__inner">
          <a href="#top" className="nav__brand" onClick={() => setMenuOpen(false)}>
            <span className="nav__logo" aria-hidden="true"><IcLogo /></span>
            <span className="nav__name">sentryl<span className="nav__dot">.</span></span>
          </a>

          <nav className="nav__links" aria-label="Primary">
            {NAV_LINKS.map(([href, label]) => (
              <a key={href} href={href} className={active === href.slice(1) ? 'is-active' : ''}
                 onClick={() => setMenuOpen(false)}>{label}</a>
            ))}
          </nav>

          <div className="nav__cta">
            <a className="btn btn--ghost" href={REPO} target="_blank" rel="noopener">
              <IcGithub /><span>GitHub</span>
            </a>
            <button className="nav__burger" aria-label="Toggle menu" aria-expanded={menuOpen}
                    onClick={() => setMenuOpen((o) => !o)}>
              <span /><span /><span />
            </button>
          </div>
        </div>
      </header>

      <main id="top">
        {/* ===================== HERO ===================== */}
        <section className="hero">
          <ParticleField />
          <div className="hero__glow" aria-hidden="true" />

          <div className="hero__inner">
            <p className="hero__kicker reveal">Real-time streaming · anomaly detection</p>

            <h1 className="hero__title reveal">
              Catching the{' '}
              <span className="mark">
                one bad signal
                <svg className="mark__wave" viewBox="0 0 220 18" preserveAspectRatio="none" aria-hidden="true">
                  <path d="M2 12 H46 L54 12 L62 3 L72 16 L80 9 L90 12 H132 L140 12 L150 11 L162 12 H218"
                        fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
              <br />
              in <span className="count" data-target="10000">0</span> sensors,{' '}
              <span className="nowrap">every second.</span>
            </h1>

            <p className="hero__sub reveal">
              A production-grade pipeline that ingests <strong>10,000+ IoT sensors</strong>, extracts streaming
              features in <strong>sliding windows</strong>, and flags anomalies with an <strong>LSTM Autoencoder</strong>{' '}
              — end to end, in under a second, on 100% open-source infrastructure.
            </p>

            <div className="hero__actions reveal">
              <a className="btn btn--primary" href={REPO} target="_blank" rel="noopener">
                Explore the source <IcArrow />
              </a>
              <a className="btn btn--ghost" href="#architecture">See how it works</a>
            </div>

            <dl className="hero__stats reveal">
              <div className="stat"><dt>Throughput</dt><dd><span className="count" data-target="10000">0</span><span className="stat__unit">events/sec</span></dd></div>
              <div className="stat"><dt>End-to-end latency</dt><dd>&lt;<span className="count" data-target="1">0</span><span className="stat__unit">second (p95)</span></dd></div>
              <div className="stat"><dt>Detection rate</dt><dd><span className="count" data-target="95">0</span><span className="stat__unit">%+</span></dd></div>
              <div className="stat"><dt>Proprietary tools</dt><dd><span className="count" data-target="0">0</span><span className="stat__unit">vendor lock-in</span></dd></div>
            </dl>
          </div>

          <a href="#challenge" className="hero__scroll" aria-label="Scroll down"><span /></a>
        </section>

        {/* ===================== CHALLENGE ===================== */}
        <section className="section" id="challenge">
          <div className="section__head reveal">
            <p className="eyebrow">01 — The problem</p>
            <h2>Why processing 10,000 sensors in real time is genuinely hard</h2>
            <p className="section__lead">
              Most tutorials show ten sensors and a polling loop. Real fleets have thousands of devices that never
              stop talking — and they won't wait for a single-threaded script to catch up. Four constraints push
              against each other at the same time.
            </p>
          </div>

          <div className="cards-grid">
            {[
              ['×10K', 'Volume', '10,000 sensors emitting one reading per second is 10,000 events/second, sustained, forever. Ingestion has to be horizontally parallel from message one.'],
              ['<1s', 'Latency', 'An anomaly is only useful if you hear about it now. The entire path — ingest, window, featurize, score — has to close in under a second at p95.'],
              ['95%+', 'Accuracy', 'Catch the real failures without drowning operators in false alarms. That means modeling time, not just thresholding raw values.'],
              ['$0', 'Cost', 'No managed cloud bill. Every component is open-source and runs on a single beefy box for dev, or a small Kubernetes cluster for production.'],
            ].map(([num, title, body], i) => (
              <article className="card reveal" style={stagger(i)} key={title}>
                <span className="card__num">{num}</span>
                <h3>{title}</h3>
                <p>{body}</p>
              </article>
            ))}
          </div>
        </section>

        {/* ===================== ARCHITECTURE ===================== */}
        <section className="section section--alt" id="architecture">
          <div className="section__head reveal">
            <p className="eyebrow">02 — System design</p>
            <h2>One stream, six moving parts, zero glue scripts</h2>
            <p className="section__lead">
              Data flows in one direction: from simulated sensors through Kafka, into Spark for windowed feature
              extraction, out to a served LSTM model for scoring, then fanned out to alerting, durable storage, and
              live dashboards. Every hop is independently scalable.
            </p>
          </div>

          <div className="diagram reveal" id="diagram">
            <div className="instr__bar">
              <span className="instr__id">Fig.01 — end-to-end dataflow</span>
              <span className="instr__live"><i />streaming</span>
            </div>

            <div className="diagram__row">
              <Node icon={<IcSensor />} kicker="Source" title="10K Sensors" sub="async simulator" />
              <Flow />
              <Node icon={<IcKafka />} kicker="Transport" title="Kafka" sub="raw-readings · KRaft" />
              <Flow />
              <Node icon={<IcSpark />} kicker="Processing" title="Spark Streaming" sub="sliding-window features" />
              <Flow />
              <Node icon={<IcModel />} kicker="Inference" title="TF-Serving" sub="LSTM Autoencoder" />
            </div>

            <div className="diagram__fan" aria-hidden="true">
              <span className="fanline" /><span className="fanline" /><span className="fanline" />
            </div>

            <div className="diagram__row diagram__row--sinks">
              <Node sink warn icon={<IcAlert />} kicker="Alerting" title="Kafka · anomalies" sub="downstream consumers" />
              <Node sink icon={<IcStorage />} kicker="Storage" title="MinIO" sub="Parquet · features + scores" />
              <Node sink icon={<IcMonitor />} kicker="Observability" title="Prometheus + Grafana" sub="live metrics & dashboards" />
            </div>
          </div>

          <p className="diagram__caption reveal">
            Fault tolerance is built in: Kafka persists the log, Spark checkpoints its state, and TF-Serving is
            stateless — any component can restart without losing data.
          </p>
        </section>

        {/* ===================== PIPELINE ===================== */}
        <section className="section" id="pipeline">
          <div className="section__head reveal">
            <p className="eyebrow">03 — Walkthrough</p>
            <h2>Following a single reading through the system</h2>
            <p className="section__lead">
              A reading is born on a sensor and dies as a dashboard line. Here's every stop it makes — and the
              engineering decision behind each one.
            </p>
          </div>

          <ol className="timeline">
            <TimelineItem n={1} title="Ingestion — an async sensor fleet" tag="aiokafka · Python">
              <p>
                The producer simulates thousands of sensors with a single asyncio event loop instead of thousands of
                threads. Each tick fires one reading per sensor concurrently and awaits the whole batch —
                gzip-compressed, keyed by <code>sensor_id</code> so a device's history stays on one partition.
              </p>
              <CodeSendBatch />
            </TimelineItem>

            <TimelineItem n={2} title="Transport — Kafka in KRaft mode" tag="Kafka 3.6 · no ZooKeeper">
              <p>
                Readings land on the <code>raw-readings</code> topic (10 partitions) as JSON. Running Kafka in KRaft
                mode removes the ZooKeeper dependency entirely — one less stateful service to babysit. Partitions are
                the unit of parallelism: more partitions, more Spark tasks reading in parallel.
              </p>
              <CodeJson />
            </TimelineItem>

            <TimelineItem n={3} title="Processing — sliding-window feature extraction" tag="Spark Structured Streaming">
              <p>
                Raw values are noisy; <em>statistics</em> tell the story. Spark groups the stream into{' '}
                <strong>60-second windows that slide every 10 seconds</strong> and, per sensor, computes the six
                features the model expects. A watermark bounds how long it waits for late data.
              </p>
              <CodeWindow />
            </TimelineItem>

            <TimelineItem n={4} title={'Inference — scoring against “normal”'} tag="TensorFlow Serving">
              <p>
                Each window's feature vector is sent to the LSTM Autoencoder over TF-Serving's REST API. The model
                reconstructs the input; a high reconstruction error means the pattern doesn't look like anything it
                learned as normal — that's the anomaly score.
              </p>
            </TimelineItem>

            <TimelineItem n={5} title="Fan-out — alert, store, observe" tag="Kafka · MinIO · Prometheus">
              <p>
                Scored windows split three ways: anomalies are published to the <code>anomalies</code> topic for
                downstream consumers, every feature+score row is persisted to MinIO as Parquet for replay and
                retraining, and counters/histograms are exported to Prometheus and visualized in Grafana.
              </p>
            </TimelineItem>
          </ol>
        </section>

        {/* ===================== MODEL ===================== */}
        <section className="section section--alt" id="model">
          <div className="section__head reveal">
            <p className="eyebrow">04 — The machine learning</p>
            <h2>An LSTM Autoencoder that learns {'“'}normal,{'”'} then notices when it's broken</h2>
            <p className="section__lead">
              IoT data is time-series — what happened five minutes ago matters. Rather than label every kind of
              failure up front, the model learns the shape of healthy data and treats poor reconstruction as the
              signal. Anything it can't faithfully rebuild is, by definition, unusual.
            </p>
          </div>

          <div className="model">
            <div className="model__diagram reveal">
              <div className="instr__bar">
                <span className="instr__id">Fig.02 — reconstruction model</span>
                <span className="instr__live instr__live--idle"><i />mse loss</span>
              </div>
              <div className="ae">
                <div className="ae__stack ae__stack--enc">
                  <span className="ae__label">Encoder</span>
                  <div className="ae__layer" style={{ ['--w']: '100%' } as CSSProperties}>Input · 50 × 6</div>
                  <div className="ae__layer" style={{ ['--w']: '80%' } as CSSProperties}>LSTM · 128</div>
                  <div className="ae__layer" style={{ ['--w']: '55%' } as CSSProperties}>LSTM · 64</div>
                </div>
                <div className="ae__bottleneck"><span>latent</span></div>
                <div className="ae__stack ae__stack--dec">
                  <span className="ae__label">Decoder</span>
                  <div className="ae__layer" style={{ ['--w']: '55%' } as CSSProperties}>RepeatVector</div>
                  <div className="ae__layer" style={{ ['--w']: '80%' } as CSSProperties}>LSTM · 64 → 128</div>
                  <div className="ae__layer" style={{ ['--w']: '100%' } as CSSProperties}>TimeDistributed · 6</div>
                </div>
              </div>
              <p className="model__hint">
                Trained on synthetic healthy data with <code>mse</code> loss, early stopping, and an adaptive
                learning-rate schedule. The reconstruction error distribution sets the anomaly threshold (95th
                percentile by default).
              </p>
            </div>

            <div className="model__copy reveal">
              <h3>The four failure modes it's tuned to catch</h3>
              <ul className="anomalies">
                {[
                  ['spike', 'Spike', 'A sudden jump or drop — a sensor reading 50°C when it should read 25°C.'],
                  ['drift', 'Drift', 'A slow, sustained creep away from baseline over many windows — early hardware degradation.'],
                  ['stuck', 'Stuck', 'A frozen value with zero variance — the classic dead-sensor failure signature.'],
                  ['noise', 'Noise', 'Erratic high-variance readings from electrical interference or a failing connection.'],
                ].map(([shape, title, body]) => (
                  <li key={shape}>
                    <span className="anomalies__spark" data-shape={shape} aria-hidden="true" />
                    <div><strong>{title}</strong><p>{body}</p></div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* ===================== RESULTS ===================== */}
        <section className="section" id="results">
          <div className="section__head reveal">
            <p className="eyebrow">05 — What it delivers</p>
            <h2>The numbers the system is built to hit</h2>
            <p className="section__lead">
              Performance targets validated against the design: high throughput, sub-second latency, and a model
              evaluated on ROC-AUC, PR-AUC, precision, recall, and F1.
            </p>
          </div>

          <div className="metrics reveal">
            <div className="metric"><span className="metric__val"><span className="count" data-target="10000">0</span></span><span className="metric__label">events / second sustained</span></div>
            <div className="metric"><span className="metric__val">&lt;<span className="count" data-target="1">0</span>s</span><span className="metric__label">end-to-end latency (p95)</span></div>
            <div className="metric"><span className="metric__val"><span className="count" data-target="95">0</span>%+</span><span className="metric__label">anomaly detection rate</span></div>
            <div className="metric"><span className="metric__val"><span className="count" data-target="99">0</span>.9%</span><span className="metric__label">target availability</span></div>
          </div>

          <div className="features-grid reveal">
            {[
              ['Fault tolerant', 'Kafka log persistence + Spark checkpointing means a crash resumes exactly where it left off.'],
              ['Horizontally scalable', 'Add Kafka partitions, Spark workers, or producer instances to scale past 10K with no code changes.'],
              ['Fully observable', 'Events, latency, anomaly counts, precision and recall are all exported and dashboarded from day one.'],
              ['Reproducible', 'One docker-compose up for local dev; seven Kubernetes manifests for production scale.'],
            ].map(([h, p]) => (
              <div className="feature" key={h}><h4>{h}</h4><p>{p}</p></div>
            ))}
          </div>
        </section>

        {/* ===================== STACK ===================== */}
        <section className="section section--alt" id="stack">
          <div className="section__head reveal">
            <p className="eyebrow">06 — The toolbox</p>
            <h2>Built entirely on open-source infrastructure</h2>
            <p className="section__lead">
              No proprietary services, no vendor lock-in — every layer is something you can run yourself.
            </p>
          </div>

          <div className="stack-grid">
            {[
              ['Apache Kafka', 'Streaming transport · KRaft'],
              ['Apache Spark', 'Structured Streaming'],
              ['TensorFlow', 'LSTM Autoencoder'],
              ['TF-Serving', 'Real-time inference'],
              ['MinIO', 'S3-compatible storage'],
              ['Prometheus', 'Metrics collection'],
              ['Grafana', 'Dashboards'],
              ['Docker', 'Containerization'],
              ['Kubernetes', 'Orchestration · k3s'],
              ['Python · asyncio', 'Async producer'],
            ].map(([name, sub], i) => (
              <div className="tech reveal" style={stagger(i)} key={name}><strong>{name}</strong><span>{sub}</span></div>
            ))}
          </div>

          <div className="deploy reveal">
            <div className="deploy__col">
              <h3>Local — for the sane</h3>
              <div className="code code--block"><pre>{`# spin up the entire stack
docker-compose up -d

# train the model + run the demo
.\\scripts\\setup.ps1
.\\scripts\\run_demo.ps1`}</pre></div>
            </div>
            <div className="deploy__col">
              <h3>Production — for scale</h3>
              <div className="code code--block"><pre>{`# apply the k8s manifests
kubectl apply -f k8s/

# scale any tier independently
kubectl scale deploy spark-worker --replicas=5`}</pre></div>
            </div>
          </div>
        </section>

        {/* ===================== CTA ===================== */}
        <section className="cta reveal">
          <div className="cta__inner">
            <h2>Read the code. Run the demo. See it work.</h2>
            <p>
              The full system — producer, streaming job, training pipeline, K8s manifests, tests, and dashboards —
              is open-source and documented.
            </p>
            <div className="hero__actions">
              <a className="btn btn--primary" href={REPO} target="_blank" rel="noopener">View the repository</a>
              <a className="btn btn--ghost" href="#top">Back to top</a>
            </div>
          </div>
        </section>
      </main>

      {/* ===================== FOOTER ===================== */}
      <footer className="footer">
        <div className="footer__inner">
          <div className="footer__brand">
            <span className="nav__name">sentryl<span className="nav__dot">.</span></span>
            <p>Real-time IoT anomaly detection — a streaming data-engineering & ML system.</p>
          </div>
          <div className="footer__links">
            <a href={REPO} target="_blank" rel="noopener">GitHub</a>
            <a href={USER} target="_blank" rel="noopener">@yassnemo</a>
            <a href="#top">Top</a>
          </div>
        </div>
        <p className="footer__fine">Designed & engineered by Yassine Erradouani · MIT Licensed</p>
      </footer>
    </div>
  )
}

/* ---------- small building blocks ---------- */

function Node({ icon, kicker, title, sub, sink, warn }: {
  icon: ReactNode; kicker: string; title: string; sub: string; sink?: boolean; warn?: boolean
}) {
  return (
    <div className={`node${sink ? ' node--sink' : ''}`}>
      <div className={`node__icon${warn ? ' node__icon--warn' : ''}`}>{icon}</div>
      <div className="node__body">
        <span className="node__kicker">{kicker}</span>
        <strong>{title}</strong>
        <small>{sub}</small>
      </div>
    </div>
  )
}

const Flow = () => <div className="flow" aria-hidden="true"><span className="flow__pkt" /></div>

function TimelineItem({ n, title, tag, children }: {
  n: number; title: string; tag: string; children: ReactNode
}) {
  return (
    <li className="timeline__item reveal">
      <div className="timeline__marker"><span>{n}</span></div>
      <div className="timeline__content">
        <div className="timeline__head">
          <h3>{title}</h3>
          <span className="tag">{tag}</span>
        </div>
        {children}
      </div>
    </li>
  )
}

/* ---------- code blocks (syntax highlighting via spans) ---------- */

const CodeSendBatch = () => (
  <div className="code"><pre>
<span className="c-kw">async def</span> <span className="c-fn">send_batch</span>(self, batch_size):{'\n'}
{'    '}tasks = []{'\n'}
{'    '}<span className="c-kw">for</span> i <span className="c-kw">in</span> <span className="c-fn">range</span>(batch_size):{'\n'}
{'        '}sensor  = self.sensors[i % <span className="c-fn">len</span>(self.sensors)]{'\n'}
{'        '}reading = sensor.<span className="c-fn">generate_reading</span>(){'\n'}
{'        '}tasks.<span className="c-fn">append</span>(self.producer.<span className="c-fn">send</span>(self.topic, value=reading,{'\n'}
{'                                        '}key=reading[<span className="c-str">'sensor_id'</span>].<span className="c-fn">encode</span>())){'\n'}
{'    '}<span className="c-kw">await</span> asyncio.<span className="c-fn">gather</span>(*tasks)   <span className="c-cm"># one thread, thousands of sends</span>
  </pre></div>
)

const CodeJson = () => (
  <div className="code"><pre>
{'{'}{'\n'}
{'  '}<span className="c-str">"sensor_id"</span>: <span className="c-str">"sensor_000042"</span>,{'\n'}
{'  '}<span className="c-str">"timestamp"</span>: <span className="c-str">"2025-10-01T10:30:00Z"</span>,{'\n'}
{'  '}<span className="c-str">"metric"</span>:    <span className="c-str">"temperature"</span>,{'\n'}
{'  '}<span className="c-str">"value"</span>:     <span className="c-num">25.5</span>,{'\n'}
{'  '}<span className="c-str">"meta"</span>: {'{'} <span className="c-str">"unit"</span>: <span className="c-str">"celsius"</span>, <span className="c-str">"location"</span>: <span className="c-str">"zone_7"</span> {'}'}{'\n'}
{'}'}
  </pre></div>
)

const CodeWindow = () => (
  <div className="code"><pre>
windowed = (df{'\n'}
{'  '}.<span className="c-fn">withWatermark</span>(<span className="c-str">"timestamp"</span>, <span className="c-str">"30 seconds"</span>){'\n'}
{'  '}.<span className="c-fn">groupBy</span>(<span className="c-fn">window</span>(col(<span className="c-str">"timestamp"</span>), <span className="c-str">"60 seconds"</span>, <span className="c-str">"10 seconds"</span>),{'\n'}
{'           '}col(<span className="c-str">"sensor_id"</span>)){'\n'}
{'  '}.<span className="c-fn">agg</span>(<span className="c-fn">avg</span>(<span className="c-str">"value"</span>),    <span className="c-fn">stddev</span>(<span className="c-str">"value"</span>),{'\n'}
{'       '}<span className="c-fn">min</span>(<span className="c-str">"value"</span>),    <span className="c-fn">max</span>(<span className="c-str">"value"</span>),{'\n'}
{'       '}<span className="c-fn">count</span>(<span className="c-str">"value"</span>)))   <span className="c-cm"># {'→'} mean, stddev, min, max, count, range</span>
  </pre></div>
)

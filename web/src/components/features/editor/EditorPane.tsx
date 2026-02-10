/**
 * EditorPane — Static code display for the Builder IDE.
 * Will be replaced by Monaco Editor integration; serves as the visual shell.
 * Shows different syntax highlighting for light vs dark mode via the
 * syn-* CSS classes defined in globals.css.
 */
export function EditorPane() {
  return (
    <div className="flex-1 overflow-auto custom-scrollbar font-mono text-sm leading-6 flex relative bg-background dark:bg-black">
      {/* Line Numbers */}
      <div className="w-12 shrink-0 text-right pr-3 select-none py-4 text-muted-foreground/50 border-r border-border/30">
        {Array.from({ length: 25 }, (_, i) => (
          <div key={i + 1}>{i + 1}</div>
        ))}
      </div>

      {/* Code Area */}
      <div className="flex-1 p-4 whitespace-pre text-foreground">
        <span className="syn-keyword">import</span> {'{ useState }'}{' '}
        <span className="syn-keyword">from</span>{' '}
        <span className="syn-string">&apos;react&apos;</span>
        {'\n'}
        <span className="syn-keyword">import</span> reactLogo{' '}
        <span className="syn-keyword">from</span>{' '}
        <span className="syn-string">&apos;./assets/react.svg&apos;</span>
        {'\n'}
        <span className="syn-keyword">import</span>{' '}
        <span className="syn-string">&apos;./App.css&apos;</span>
        {'\n\n'}
        <span className="syn-comment">
          {'// This component handles the main counter functionality'}
        </span>
        {'\n'}
        <span className="syn-keyword">function</span>{' '}
        <span className="syn-function">App</span>() {'{'}
        {'\n'}
        {'  '}
        <span className="syn-keyword">const</span> [count, setCount] ={' '}
        <span className="syn-function">useState</span>(
        <span className="syn-variable">0</span>)
        {'\n\n'}
        {'  '}
        <span className="syn-keyword">return</span> (
        {'\n'}
        {'    <'}
        <span className="syn-tag">div</span>{' '}
        <span className="syn-attr">className</span>=
        <span className="syn-string">&quot;App&quot;</span>
        {'>'}
        {'\n'}
        {'      <'}
        <span className="syn-tag">div</span>
        {'>'}
        {'\n'}
        {'        <'}
        <span className="syn-tag">a</span>{' '}
        <span className="syn-attr">href</span>=
        <span className="syn-string">&quot;https://vitejs.dev&quot;</span>{' '}
        <span className="syn-attr">target</span>=
        <span className="syn-string">&quot;_blank&quot;</span>
        {'>'}
        {'\n'}
        {'          <'}
        <span className="syn-tag">img</span>{' '}
        <span className="syn-attr">src</span>=
        <span className="syn-string">&quot;/vite.svg&quot;</span>{' '}
        <span className="syn-attr">className</span>=
        <span className="syn-string">&quot;logo&quot;</span>{' '}
        <span className="syn-attr">alt</span>=
        <span className="syn-string">&quot;Vite logo&quot;</span>
        {' />'}
        {'\n'}
        {'        </'}
        <span className="syn-tag">a</span>
        {'>'}
        {'\n'}
        {'        <'}
        <span className="syn-tag">a</span>{' '}
        <span className="syn-attr">href</span>=
        <span className="syn-string">&quot;https://reactjs.org&quot;</span>{' '}
        <span className="syn-attr">target</span>=
        <span className="syn-string">&quot;_blank&quot;</span>
        {'>'}
        {'\n'}
        {'          <'}
        <span className="syn-tag">img</span>{' '}
        <span className="syn-attr">src</span>
        ={'{'} reactLogo {'}'}{' '}
        <span className="syn-attr">className</span>=
        <span className="syn-string">&quot;logo react&quot;</span>
        {' />'}
        {'\n'}
        {'        </'}
        <span className="syn-tag">a</span>
        {'>'}
        {'\n'}
        {'      </'}
        <span className="syn-tag">div</span>
        {'>'}
        {'\n'}
        {'      <'}
        <span className="syn-tag">h1</span>
        {'>'}Vite + React{'</'}
        <span className="syn-tag">h1</span>
        {'>'}
        {'\n'}
        {'      <'}
        <span className="syn-tag">div</span>{' '}
        <span className="syn-attr">className</span>=
        <span className="syn-string">&quot;card&quot;</span>
        {'>'}
        {'\n'}
        {'        <'}
        <span className="syn-tag">button</span>{' '}
        <span className="syn-attr">onClick</span>
        {'={() => '}
        <span className="syn-function">setCount</span>
        {'((count) => count + '}
        <span className="syn-variable">1</span>
        {')}>'}
        {'\n'}
        {'          count is {count}'}
        <span className="animate-pulse bg-cf-primary/80 w-[2px] h-4 inline-block align-middle ml-0.5" />
        {'\n'}
        {'        </'}
        <span className="syn-tag">button</span>
        {'>'}
        {'\n'}
        {'      </'}
        <span className="syn-tag">div</span>
        {'>'}
        {'\n'}
        {'    </'}
        <span className="syn-tag">div</span>
        {'>'}
        {'\n'}
        {'  )'}
        {'\n'}
        {'}'}
        {'\n\n'}
        <span className="syn-keyword">export default</span>{' '}
        <span className="syn-function">App</span>
      </div>

      {/* Minimap mock (dark mode only) */}
      <div className="w-16 shrink-0 bg-black/30 border-l border-border/20 hidden lg:dark:block opacity-60 pointer-events-none">
        {[8, 10, 6, 0, 10, 8, 12, 10].map((w, i) =>
          w === 0 ? (
            <div key={i} className="h-4" />
          ) : (
            <div
              key={i}
              className="h-1 bg-muted-foreground/20 my-1 mx-auto rounded"
              style={{ width: `${w * 4}px` }}
            />
          )
        )}
        <div className="h-20 w-full bg-muted/10 my-2" />
      </div>
    </div>
  )
}

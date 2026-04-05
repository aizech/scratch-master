# Browser Automation for Scratch

Test and verify Scratch projects created with ScratchGen using Playwright.

---

## Editor URLs

| Purpose | URL |
|---------|-----|
| Editor (new project) | `https://scratch.mit.edu/projects/editor/` |
| Editor (load project) | `https://scratch.mit.edu/projects/{project_id}/` |
| Player only | `https://scratch.mit.edu/projects/{project_id}/player/` |
| Turbowarp (faster) | `https://turbowarp.org/{project_id}/editor` |
| Turbowarp Player | `https://turbowarp.org/{project_id}/player` |

---

## Installation

```bash
pip install playwright
playwright install chromium
```

---

## Basic Workflow

1. **Upload .sb3** → Import project to Scratch editor
2. **Click green flag** → Run project
3. **Verify behavior** → Check stage output, console logs
4. **Capture screenshot** → Document results

---

## Playwright Patterns

### Open Editor with Project

```python
from playwright.sync_api import sync_playwright
import sys

def load_project(sb3_path: str):
    """Load .sb3 file into Scratch editor."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Open editor
        page.goto("https://scratch.mit.edu/projects/editor/")
        page.wait_for_load_state("networkidle")
        
        # Note: Direct file upload to Scratch requires API authentication
        # For testing, use Turbowarp which supports file upload
        page.goto(f"https://turbowarp.org/editor")
        
        # Wait for VM to be ready before interacting
        page.wait_for_function("() => typeof window.vm !== 'undefined'")

        # TurboWarp uses drag-and-drop upload, not a visible <input>.
        # Trigger via the File menu instead:
        page.click("[aria-label='File']")       # Open File menu
        page.wait_for_selector("text=Load from your computer")
        with page.expect_file_chooser() as fc:
            page.click("text=Load from your computer")
        fc.value.set_files(sb3_path)
        page.wait_for_timeout(2000)
        
        browser.close()

if __name__ == "__main__":
    load_project(sys.argv[1])
```

### Run and Capture Output

```python
from playwright.sync_api import sync_playwright

def run_project(project_url: str):
    """Run project and capture stage output."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}"))
        
        page.goto(project_url)
        page.wait_for_load_state("networkidle")
        
        # Wait for VM and green flag (use stable selector, not hashed CSS class)
        page.wait_for_function("() => typeof window.vm !== 'undefined'")
        page.wait_for_selector("[title='Go']", timeout=10000)
        
        # Click green flag to start
        page.click("[title='Go']")
        
        # Let it run for a few seconds
        page.wait_for_timeout(3000)
        
        # Take screenshot
        page.screenshot(path="output.png")
        
        browser.close()
```

### Verify Sprite Movement

```python
from playwright.sync_api import sync_playwright
from PIL import Image
import io

def verify_movement(project_path: str, expected_x: float, tolerance: float = 10):
    """Verify sprite moved to expected X position."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Open in Turbowarp (supports file upload)
        page.goto("https://turbowarp.org/editor")
        
        # Upload project
        page.set_input_files('input[type="file"]', [project_path])
        page.wait_for_timeout(3000)
        
        # Get initial position from VM
        page.evaluate("""() => {
            const vm = window.vm;
            const sprite = vm.runtime.targets.find(t => !t.isStage);
            return { x: sprite.x, y: sprite.y };
        }""")
        
        # Run project (use VM API or stable selector — NOT hashed CSS classes)
        page.wait_for_function("() => typeof window.vm !== 'undefined'")
        page.click("[title='Go']")
        page.wait_for_timeout(1000)
        
        # Get final position
        final_pos = page.evaluate("""() => {
            const vm = window.vm;
            const sprite = vm.runtime.targets.find(t => !t.isStage);
            return { x: sprite.x, y: sprite.y };
        }""")
        
        print(f"Sprite position: {final_pos}")
        
        # Verify X position
        if abs(final_pos['x'] - expected_x) <= tolerance:
            print("✓ Position verified")
        else:
            print(f"✗ Position mismatch: expected {expected_x}, got {final_pos['x']}")
        
        browser.close()
```

---

## Multi-Agent Tool Mapping

### Agno

```python
from agno.tools import Tool

scratch_tools = [
    Tool(
        name="run_scratch_test",
        func=run_scratch_test,
        description="Test Scratch project in browser"
    )
]
```

### OpenCode

```bash
# Use browser tools directly
mcp-playwright_browser_navigate
mcp-playwright_browser_click
mcp-playwright_browser_screenshot
```

---

## Common Patterns

### Wait for Project Load

```python
# Wait for VM to be ready
page.wait_for_function("""() => {
    return window.vm && window.vm.runtime && window.vm.runtime.targets;
}""")

# Wait for specific sprite
page.wait_for_function("""() => {
    return window.vm.runtime.targets.some(t => t.name === 'Sprite1');
}""")
```

### Get Project State

```python
state = page.evaluate("""() => {
    const vm = window.vm;
    return {
        stage: vm.runtime.targets.find(t => t.isStage),
        sprites: vm.runtime.targets.filter(t => !t.isStage).map(s => s.name),
        variables: Object.keys(vm.runtime.variables),
        lists: Object.keys(vm.runtime.lists)
    };
}""")
```

### Trigger Events

```python
# Click green flag
page.click(".green-flag")

# Press key
page.keyboard.press("Space")

# Click sprite
page.click(".scratch-stage >> .sprite")
```

### Interact with Stage

```python
# Move mouse to stage
page.hover(".scratch-stage")

# Click at coordinates
page.click(".scratch-stage", position={"x": 100, "y": 200})
```

---

## Troubleshooting

### Project Won't Load

- Use Turbowarp instead (no auth required)
- Check file format is valid `.sb3`
- Verify JSON is not corrupted

### Green Flag Not Found

```python
# Use stable attribute selectors — avoid hashed CSS classes like .green-flag_ebada2
# which change across TurboWarp builds:
page.wait_for_selector("[title='Go']")
# Or via VM API:
page.evaluate("() => window.vm.greenFlag()")
```

### VM Not Available

```python
# Wait for VM to inject
page.wait_for_function("""() => typeof window.vm !== 'undefined'""")
```

---

## Alternative: Local Testing

Use TurboWarp's standalone player:

```python
import subprocess

def test_with_turbowarp(sb3_path: str):
    """Open project in TurboWarp."""
    import webbrowser
    url = "https://turbowarp.org/editor"
    webbrowser.open(url)
    # User can then drag-drop the .sb3 file
```

Or run locally with Scratch VM:

```bash
# Install scratch-vm
npm install scratch-vm

# Create test runner
node test-runner.js project.sb3
```

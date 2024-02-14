<h1>Chunk structure</h1>

![Layers diagram](https://github.com/chromegism/iso-game-revised/blob/master/readmedata/LayersDiagram.png)

<h1>Layer Generation Process</h1>

<ul>
    <li>Load images from files</li>
    <li>Create parallel process for generation</li>
    <li>Checks if it needs to load or generate terrain</li>
    <li>If load, extracts the specified zip file and loads the terrain.npy file</li>
    <li>If generate, uses Perlin noise to generate a map with the specified dimensions</li>
    <li>Converts to raw numerical data into sdl2_sprite objects, and then groups them into Chunks using Tile_Groups</li>
    <li>Groups these chunks into a Chunk_Group object</li>
    <li>Sends back data to the main process from the subprocess</li>
    <li>Renders everything in the Chunk_Group object to be displayed on the screen</li>
</ul>
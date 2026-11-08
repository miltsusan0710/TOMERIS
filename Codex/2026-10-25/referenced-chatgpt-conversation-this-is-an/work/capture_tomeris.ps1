Add-Type -AssemblyName System.Drawing
$bounds = New-Object Drawing.Rectangle([int]$args[0],[int]$args[1],[int]$args[2],[int]$args[3])
$bitmap = New-Object Drawing.Bitmap($bounds.Width,$bounds.Height)
$graphics = [Drawing.Graphics]::FromImage($bitmap)
try {
  $graphics.CopyFromScreen($bounds.Location,[Drawing.Point]::Empty,$bounds.Size)
  $bitmap.Save($args[4],[Drawing.Imaging.ImageFormat]::Png)
} finally { $graphics.Dispose(); $bitmap.Dispose() }

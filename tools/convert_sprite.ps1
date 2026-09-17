Add-Type -AssemblyName System.Drawing
$src = Join-Path $PSScriptRoot '..\public\assets\images\xpeach-robot-sprite.png'
$tmp = Join-Path $PSScriptRoot 'sprite-source.png'
Copy-Item -LiteralPath $src -Destination $tmp -Force
$input = [System.Drawing.Bitmap]::FromFile($tmp)
$out = New-Object System.Drawing.Bitmap(1344,96,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$g = [System.Drawing.Graphics]::FromImage($out); $g.Clear([System.Drawing.Color]::Transparent); $g.InterpolationMode='NearestNeighbor'; $g.PixelOffsetMode='Half'
for($i=0;$i -lt 14;$i++) { $row=[int][math]::Floor($i/7); $col=[int]($i%7); $x=[int][math]::Round($col*$input.Width/7); $x2=[int][math]::Round(($col+1)*$input.Width/7); $y=[int][math]::Round($row*$input.Height/2); $y2=[int][math]::Round(($row+1)*$input.Height/2); $srcRect=New-Object System.Drawing.Rectangle($x,$y,([int]($x2-$x)),([int]($y2-$y))); $dstRect=New-Object System.Drawing.Rectangle(([int]($i*96)),0,96,96); $g.DrawImage($input,$dstRect,$srcRect,[System.Drawing.GraphicsUnit]::Pixel) }
$g.Dispose(); $input.Dispose(); $out.Save($src,[System.Drawing.Imaging.ImageFormat]::Png); $out.Dispose(); Remove-Item -LiteralPath $tmp -Force

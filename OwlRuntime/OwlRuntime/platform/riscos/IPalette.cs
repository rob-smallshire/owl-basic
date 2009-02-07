namespace OwlRuntime.platform.riscos
{
    public interface IPalette
    {
        System.Drawing.Color LogicalToPhysical(int logical);
    }
}
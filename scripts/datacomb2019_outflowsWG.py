################################
## LUPUS 3 Outflow Working Group
## Started by Adele Plunkett, 14 August 2019
## Will continue to update during the workshop
################################



'''
NOTE: The interferometry data were cut down to 10 channels of 1 km/s each by the following commands:
line = {“restfreq”   : ‘115.27120GHz’,
 ‘start’      : ‘-1.0km/s’,
 ‘width’      : ‘1.0km/s’,
 ‘nchan’      : 10,}
mstransform(sharedir+vis7m,‘mst_07_nchan10_start0kms.ms’,
 datacolumn=‘DATA’,outframe=‘LSRK’,mode=‘velocity’,regridms=True,keepflags=False,
 **line)
mstransform(sharedir+vis12m,‘mst_12_nchan10_start0kms.ms’,
 datacolumn=‘DATA’,outframe=‘LSRK’,mode=‘velocity’,regridms=True,keepflags=False,
 **line)
'''

datadir = '/Users/aplunket/ResearchNRAO/Meetings/DataComb2019/Lup3mms/Lup3mms_Share/' #the directory where your test data are held
vis7m = datadir+'mst_07_nchan10_start0kms.ms'
vis12m = datadir+'mst_12_nchan10_start0kms.ms'
TPfits = datadir+'TP_12CO.fits'
TPim = 'TP.image' #You choose the name of your TP image
#importfits(fitsimage=TPfits,imagename=TPim)  ## You just need to do this the first time, in order to get your TP Fits file into the CASA format (*.image)
vis12m7m = '12m7m.ms' #You choose the name of your combined interferometry image


##############
## Day 1: FEATHER 
## Generally, follow the CasaGuide https://casaguides.nrao.edu/index.php/M100_Band3_Combine_5.4
##############


# In CASA, look at mosaic map pointings
os.system('rm -rf *m_mosaic.png')
au.plotmosaic(vis12m,sourceid='0',figfile='12m_mosaic.png')
au.plotmosaic(vis7m,sourceid='0',figfile='7m_mosaic.png')

# Look at weights
# In CASA
os.system('rm -rf 7m_WT.png 12m_WT.png')
plotms(vis=vis12m,yaxis='wt',xaxis='uvdist',spw='0~2:200',
       coloraxis='spw',plotfile='12m_WT.png')
#
plotms(vis=vis7m,yaxis='wt',xaxis='uvdist',spw='0~8:200',
       coloraxis='spw',plotfile='7m_WT.png')

#We found that the SPW 7 has lower amplitudes, therefore we choose to remove that in this case
split(vis=vis7m,outputvis=vis7m+'.spl',spw='0,1,2,3,4,5,6,8',datacolumn='data')
vis7m = vis7m+'.spl'

# Concat, you could also scale weights, but the weights here look good already
os.system('rm -rf *12m7m.ms')
concat(vis=[vis12m,vis7m],concatvis=vis12m7m)
listobs(vis=vis12m7m,listfile='12m7m.listobs')


####################################
## CLEAN the interferometry data
###################################

lineimagename =  'feather' 
field='Lupus_3_MMS*' # LOOK IN THE LOG!! 
phasecenter='J2000 16h09m18.1 -39d04m44.0' ## WHO KNOWS WHERE TO FIND THIS??

lineimage = {"restfreq"   : '115.27120GHz',
  'start'      : '5.0km/s', 
  'width'      : '1.0km/s',
  'nchan'      : 4,
  'imsize'     : [900,600], #or [896,540]
  'cell'       : '0.4arcsec',
  'gridder'    : 'mosaic',
  'weighting'  : 'briggs',
  'robust'     : 0.5,
}

#First we make a "dirty" image (niter=0, or no iterations) just to see that the image parameters are OK
tclean(vis='12m7m.ms',imagename=lineimagename+'_12m_niter0',field=field,spw='',phasecenter=phasecenter,mosweight=True,specmode='cube',niter=0,interpolation='nearest',**lineimage)

#Next, RUN a deeper TCLEAN of 12m+7m
niter=10000
cniter=500 ## It was recommended to me to use a smaller (<1000) cniter, but this takes longer
gain=0.05 ## It was recommended to me to use a smaller (<0.1 default) gain, but this takes longer
threshold='5mJy' 
tclean(vis=['12m7m.ms'],imagename=lineimagename+'_7m12m',field=field,spw='',phasecenter=phasecenter,mosweight=True,specmode='cube',niter=niter,cycleniter=cniter,gain=gain,threshold=threshold,usemask='pb',pbmask=0.3,**lineimage)
## I tweaked pbmask to be slightly higher than the default (which is 0.2?) because the edges in this map may be particularly noisy, with bright emission.
## YOU can do more iterations of TCLEAN

imsmooth(imagename=lineimagename+'_7m12m.image',outfile=lineimagename+'_7m12m.imsmooth',kernel='commonbeam') #this is a trick when you need a single beam, rather than a beam per channel.  It will be necessary for the feather with TP image.
## SOME warnings liks this, but I ignore it for now: 2019-08-14 07:45:07	WARN	imsmooth::Image2DConvolver::_dealWithRestoringBeam	Convolving kernel has minor axis 0.0736102 arcsec which is less than the pixel diagonal length of 0.565685 arcsec. Thus, the kernel is poorly sampled, and so the output of this application may not be what you expect. You should consider increasing the kernel size or regridding the image to a smaller pixel size



########################
## Prepare to FEATHER
########################

#Drop the Stokes axis in both images
imsubimage(imagename=lineimagename+'_7m12m.imsmooth',dropdeg=True,outfile='IntForComb.imsmooth.dropdeg') 
imsubimage(imagename='TP.image',dropdeg=True,outfile='TPForComb.dropdeg')
#exportfits ?
#importfits ?

Intim =  'IntForComb.imsmooth.dropdeg' #12m+7m image from TCLEAN
Intpb =  lineimagename+'_7m12m.pb' #primary beam response, this was created in your previous 12m+7m TCLEAN
Intmask = lineimagename+'_7m12m.mask' #mask from TCLEAN (cutting below a certain pb value), this was created in your previous 12m+7m TCLEAN
TPim = 'TPForComb.dropdeg'

#Regrid the Inter. mask to have 1 channel
imsubimage(imagename=Intmask,
           chans='0',outfile=Intmask+'.cut',dropdeg=True)
#Regrid the Inter. PB mask to have 1 channel
imsubimage(imagename=Intpb,
           chans='0',outfile=Intpb+'.cut',dropdeg=True)

#check that rest frequencies match - Initially different. You have to use "imreframe" to set the rest frequency of the TP image to match that of 12m
imhead(TPim,mode='get',hdkey='restfreq')
imhead(Intim,mode='get',hdkey='restfreq')
imreframe(imagename=TPim,output=TPim+'.ref',outframe='lsrk',restfreq='115271199999.99998Hz')
imhead(TPim+'.ref',mode='get',hdkey='restfreq') #check again

#Regrid TP image to match Interferometry image (note that the 'Freq' and 'Stokes' axes are flipped)
imregrid(imagename=TPim+'.ref',
         template=Intim,
         axes=[0,1,2],
         output='TP.image.regrid')


#Trim the 7m+12m and (regridded) TP images
#Do this with the mask that was created in TCLEAN based on the PB (can also do with a box, as in CASAGuides)
os.system('rm -rf TP.regrid.subim')
imsubimage(imagename='TP.image.regrid',
           outfile='TP.regrid.subim',
           mask=Intmask+'.cut',stretch=True)

os.system('rm -rf Int.image.subim')
imsubimage(imagename=Intim,
           outfile='Int.image.subim',
           mask=Intmask+'.cut',stretch=True)

#CONTINUE WITH TP.regrid.subim and Int.image.subim

#Mask the PB image to match the Int/TP images
imsubimage(imagename=Intpb+'.cut',
           outfile=Intpb+'.subim',
           mask=Intmask+'.cut')

#Multiply the TP image by the 7m+12m primary beam response 
os.system('rm -rf TP.subim.depb')
immath(imagename=['TP.regrid.subim',
                  Intpb+'.subim'],
       expr='IM0*IM1',stretch=True,
       outfile='TP.subim.depb')

#I see this warning, but ignore it: 2019-08-14 07:42:02	WARN	ImageExprCalculator::compute	image units are not the same: 'Jy/beam' vs ''. Proceed with caution. Output image metadata will be copied from one of the input images since imagemd was not specified



########################
## Ready to FEATHER
########################

os.system('rm -rf Feather.image')
feather(imagename='Feather.image',
        highres='IntForComb.imsmooth.dropdeg/',
        lowres='TP.subim.depb')


######################
## Day 2: TP2VIS
## Documentation here: https://github.com/tp2vis/distribute
########################

'''
#1.0 Collect the files
#You might need this, in case you started again.
datadir = '/Users/aplunket/ResearchNRAO/Meetings/DataComb2019/Lup3mms/Lup3mms_Share/' #the directory where your test data are held
vis7m = datadir+'mst_07_nchan10_start0kms.ms'
vis12m = datadir+'mst_12_nchan10_start0kms.ms'
TPfits = datadir+'TP_12CO.fits'
TPim = 'TP.image' #You choose the name of your TP image
#importfits(fitsimage=TPfits,imagename=TPim)  ## You just need to do this the first time, in order to get your TP Fits file into the CASA format (*.image)
vis12m7m = '12m7m.ms' #You choose the name of your combined interferometry image
'''

#1.1: Make a pointing (ptg) file
listobs(vis12m,listfile='calibrated_12m.log')
'''!cat calibrated_12m.log | grep "none" | awk '{print $4,$5}' | sed 's/\([0-9]*\)\:\([0-9]*\):\([0-9.]*\) /\1h\2m\3 /' | sed 's/\([0-9][0-9]\)\.\([0-9][0-9]\)\.\([0-9][0-9]\)\./\1d\2m\3\./' | awk '{printf("J2000 %ss %ss\n",$1,$2)}' > 12.ptg
'''
#1.2: Find a reasonable RMS
TPrms=imstat(TPim,axes=[0,1])['rms'][20:30].mean() #remember, these are the channels of the SD image (which has more than 10 channels)
print('#TP rms: {}'.format(TPrms))
#TP rms: 0.188200941992

#2. Run TP2VIS:
#You may need to: execfile('distribute/tp2vis.py')                                          # load tp2vis 
tp2vis(TPim,'tp.ms','12.ptg',rms=TPrms)                     # make visibilities, winpix is important if emission around edges
tp2vis(TPim,'tp_winpix9.ms','12.ptg',rms=TPrms, winpix=9)            # Again, make visibilities, winpix is important if emission around edges

#2.1 Check the tclean of the TP *.ms file, with niter=0
lineimagename =  'tp2vis'
field='Lupus_3_MMS*' # science field(s). 
phasecenter='J2000 16h09m18.1 -39d04m44.0'

lineimage = {"restfreq"   : '115.27120GHz',
  'start'      : '0.0km/s', 
  'width'      : '1.0km/s',
  'nchan'      : 4,
  'imsize'     : [900,600], #[896,540]
  'cell'       : '0.4arcsec',
  'gridder'    : 'mosaic',
  'weighting'  : 'briggs',
  'robust'     : 0.5,
}

tclean(vis=['tp.ms'],imagename=lineimagename+'_wp0_niter0',field=field,spw='',phasecenter=phasecenter,mosweight=True,specmode='cube',niter=0,interpolation='nearest',**lineimage)

## IF OK, the you should add the 12m and 7m visibilities as input to TCLEAN.

######################
## Day 3: SDInt
## Documentation here: https://github.com/urvashirau/WidebandSDINT
########################

## NOT WORKING YET: execfile('/Users/aplunket/ResearchNRAO/Meetings/DataComb2019/dc2019/scripts/make_gauss_beam_cube.py')
## INstead I use the PSF from TP2VIS+Tclean

## FILE List FOR runsdint.py:
vis = '12m7m.ms'
sdimage = 'TP.image' ## Original, with ra,dec,freq,stokes
sdpsf = 'tp2vis_wp0_niter0.psf' ## Need to drop the degenerate axis

## CHECK HEADER DIMENSIONS
axim = imhead(sdimage)['axisnames']
axpsf = imhead(sdpsf)['axisnames']
print('Image axes; PSF axes: {} {}'.format(axim,axpsf))

## Switch Stokes and Freq axis so that dimensions = [ra,dec,freq,stokes] for convenience in CASA
imtrans(imagename='TP.image',outfile='TP.image.trans',order='0132')   # switch stokes (2) and freq (3) axes
sdimage = 'TP.image.trans' ## Dropped the degenerate axis


## Cut the SD image to have the same number of frequency channels as the PSF 
shapeim = imhead(sdimage)['shape']
shapepsf = imhead(sdpsf)['shape']
print('Image shape; PSF Shape: {} {}'.format(shapeim,shapepsf))
imregrid(imagename=sdimage,
         template=sdpsf,
         axes=[3],
         output=sdimage+'.regrid')
## Check again:
shapeim = imhead(sdimage+'.regrid')['shape']
shapepsf = imhead(sdpsf)['shape']
print('Image shape; PSF Shape: {} {}'.format(shapeim,shapepsf))

#### FINALLY, Use these parameters in runsdint.py
vis = '12m7m.ms'
sdimage = 'TP.image.trans.regrid' ## Dropped the degenerate axis
sdpsf = 'tp2vis_wp0_niter0.psf' ## Need to drop the degenerate axis

deconvolver='hogbom'
specmode='cube'
gridder='mosaic'

phasecenter='J2000 16h09m18.1 -39d04m44.0'
imsize=[900,600]
cell='0.4arcsec'
reffreq='115.27120GHz'
dishdia=12.0 # in meters
niter=10000
cycleniter= 500
scales=[0,12,20,40,60,80,100]
pblimit=0.2
mythresh='5mJy'
mask=''
nchan=4
start='0.0km/s'
width='1.0km/s'

## We should also try to use the same parameters across the previous cleans, in order to make a really careful comparison.
## This last clean was done with multi-scale, while the others were not.





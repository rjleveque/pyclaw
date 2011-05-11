#!/usr/bin/env python
# encoding: utf-8
r"""
Module containing petclaw grid.

:Authors:
    Amal Alghamdi
    David Ketcheson
    Aron Ahmadia
"""
# ============================================================================
#      Copyright (C) 2010 David I. Ketcheson <david.ketcheson@kaust.edu.sa>
#
#  Distributed under the terms of the Berkeley Software Distribution (BSD) 
#  license
#                     http://www.opensource.org/licenses/
# ============================================================================

import numpy as np
import pyclaw.grid


# ============================================================================
#  Dimension Object
# ============================================================================
class Dimension(pyclaw.grid.Dimension):
    r"""
    Basic class representing a dimension of a Grid object

    The only difference between PyClaw and PetClaw grids are the
    boundary conditions.
    
    :Initialization:
    
    Input:
     - *name* - (string) string Name of dimension
     - *lower* - (float) Lower extent of dimension
     - *upper* - (float) Upper extent of dimension
     - *n* - (int) Number of grid cells
     - *units* - (string) Type of units, used for informational purposes only
     - *mthbc_lower* - (int) Lower boundary condition method to be used
     - *mthbc_upper* - (int) Upper boundary condition method to be used
     
        
    Output:
     - (:class:`Dimension`) - Initialized Dimension object
    """

    def edge():
        doc = r"""(ndarrary(:)) - Location of all grid cell edge coordinates
        for this dimension"""
        def fget(self): 
            if self._edge is None:
                self._edge = np.empty(self.nend-self.nstart+1)
                for i in xrange(self.nstart,self.nend+1):
                    self.edge[i] = self.lower + i*self.d
            return self._edge
        return locals()
    edge = property(**edge())
    _edge = None

    def centerghost():
        doc = r"""(ndarrary(:)) - Location of all grid cell center coordinates
        for this dimension, including ghost cells"""
        def fget(self): 
            mbc=self.mbc
            if self._centerghost is None:
                self._centerghost = np.empty(self.nend-self.nstart+2*mbc)
                for i in xrange(self.nstart-mbc,self.nend+mbc):
                    self.centerghost[i-self.nstart+mbc] = self.lower + (i+0.5)*self.d
            return self._centerghost
        return locals()
    centerghost = property(**centerghost())
    _centerghost = None

    def center():
        doc = r"""(ndarrary(:)) - Location of all grid cell center coordinates
        for this dimension"""
        def fget(self): 
            if self._center is None:
                self._center = np.empty(self.nend-self.nstart)
                for i in xrange(self.nstart,self.nend):
                    self.center[i-self.nstart] = self.lower + (i+0.5)*self.d
            return self._center
        return locals()
    center = property(**center())
    _center = None



# ============================================================================
#  petclaw Grid object definition
# ============================================================================
class Grid(pyclaw.grid.Grid):
    r"""
    Basic representation of a single grid in petclaw

    The only difference between PetClaw grid and PyClaw grid is
    the definition of q(), local_n(), __getstate__(), 
    and __setstate__().
    
    :Dimension information:
    
        Each dimension has an associated name with it that can be accessed via
        that name such as ``grid.x.n`` which would access the x dimension's
        number of grid cells.
    
    :Global Grid information:
    
        Each grid has a value for :attr:`level`, :attr:`gridno`, :attr:`t`, 
        :attr:`mbc`, :attr:`meqn` and :attr:`aux_global`.  These correspond
        to global grid traits and determine many of the properties and sizes
        of the data arrays.
        
    :Grid Data:
    
        The arrays :attr:`q`, :attr:`aux` and :attr:`capa` have variable 
        extents based on the set of dimensions present and the values of 
        :attr:`meqn` and :attr:`maux`.  Note that these are initialy set to 
        None so need to be instantiated.  For convenience, the methods
        :meth:`emtpy_q`, :meth:`ones_q`, and :meth:`zeros_q` for ``q`` and
        :meth:`emtpy_aux`, :meth:`ones_aux`, and :meth:`zeros_aux` for ``aux``
        are provided to initialize these arrays.  The :attr:`capa` array is 
        initially set to all ``1.0`` and needs to be manually set.
        
    :Properties:

        If the requested property has multiple values, a list will be returned
        with the corresponding property belonging to the dimensions in order.
         
    :Initialization:
    
        Input:
         - *dimensions* - (list of :class:`Dimension`) Dimensions that are to 
           be associated with this grid
            
        Output:
         - (:class:`Grid`) Initialized grid object
    """

    # ========== Property Definitions ========================================
    def local_n():
        def fget(self):
            #Amal doc
            shape = [i[1]-i[0] for i in self.q_da.getRanges()]
            return shape
        return locals()
    def q():
        def fget(self):
            q_dim = self.local_n
            q_dim.insert(0,self.meqn)
            q=self.gqVec.getArray().reshape(q_dim, order = 'F')
            return q
        def fset(self,q):
            if self.gqVec is None: self.init_q_petsc_structures()
            self.gqVec.setArray(q.reshape([-1], order = 'F'))
        return locals()

    local_n     = property(**local_n())
    q           = property(**q())
    
    # ========== Class Methods ===============================================
    def __init__(self,dimensions):
        r"""
        Instantiate a PCGrid object

        Here we duplicate the __init__ function from the parent class Grid.
        
        Really we should just do this:

        super(Grid,self).__init__(dimensions)

        But the problem is that Grid.__init__() sets q=None, messing up
        our use of q as a property.  We should find a better way to
        resolve this.

        See :class:`petclaw.Grid` for more info.
        """
        from pyclaw.grid import default_mapc2p
        
        # ========== Attribute Definitions ===================================
        self.level = 1
        r"""(int) - AMR level this grid belongs to, ``default = 1``"""
        self.gridno = 1
        r"""(int) - Grid number of current grid, ``default = 0``"""
        self.t = 0.0
        r"""(float) - Current time represented on this grid, 
            ``default = 0.0``"""
        self.mbc = 2
        r"""(int) - Number of ghost cells along the boundaries, 
            ``default = 2``"""
        self.meqn = 1
        r"""(int) - Dimension of q array for this grid, ``default = 1``"""
        self.aux = None
        r"""(ndarray(...,maux)) - Auxiliary array for this grid containing per 
            cell information"""
        self.capa = None
        r"""(ndarray(...)) - Capacity array for this grid, ``default = 1.0``"""
        self.aux_global = {}
        r"""(dict) - Dictionary of global values for this grid, 
            ``default = {}``"""
        self.mapc2p = default_mapc2p
        r"""(func) - Grid mapping function"""

        self.q_da = None
        self.gqVec = None
        self.lqVec = None

        # Dimension parsing
        if isinstance(dimensions,Dimension): dimensions = [dimensions]
        self._dimensions = []
        for dim in dimensions: self.add_dimension(dim)


    def init_q_petsc_structures(self):
        r"""
        Initializes PETSc structures for q. It initializes q_da, gqVec and lqVec,
        and also sets up nstart, nend, and mbc for the dimensions.
        
        """
        from petsc4py import PETSc

        #Due to the way PETSc works, we just make the grid always periodic,
        #regardless of the boundary conditions actually selected.
        #This works because in solver.qbc() we first call globalToLocal()
        #and then impose the real boundary conditions (if non-periodic).

        if hasattr(PETSc.DA, 'PeriodicType'):
            if self.ndim == 1:
                periodic_type = PETSc.DA.PeriodicType.X
            elif self.ndim == 2:
                periodic_type = PETSc.DA.PeriodicType.XY
            elif self.ndim == 3:
                periodic_type = PETSc.DA.PeriodicType.XYZ
            else:
                raise Exception("Invalid number of dimensions")
            self.q_da = PETSc.DA().create(dim=self.ndim,
                                          dof=self.meqn,
                                          sizes=self.n, 
                                          periodic_type = periodic_type,
                                          #stencil_type=self.STENCIL,
                                          stencil_width=self.mbc,
                                          comm=PETSc.COMM_WORLD)
        else:
            self.q_da = PETSc.DA().create(dim=self.ndim,
                                          dof=self.meqn,
                                          sizes=self.n, 
                                          boundary_type = PETSc.DA.BoundaryType.PERIODIC,
                                          #stencil_type=self.STENCIL,
                                          stencil_width=self.mbc,
                                          comm=PETSc.COMM_WORLD)

        self.gqVec = self.q_da.createGlobalVector()
        self.lqVec = self.q_da.createLocalVector()

        #Now set up the local indices:
        ranges = self.q_da.getRanges()
        for i,nrange in enumerate(ranges):
            self.dimensions[i].nstart=nrange[0]
            self.dimensions[i].nend  =nrange[1]
            self.dimensions[i].mbc=self.mbc